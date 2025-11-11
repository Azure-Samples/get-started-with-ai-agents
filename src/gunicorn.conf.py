# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license.
# See LICENSE file in the project root for full license information.
from typing import Dict, List, Optional

import asyncio
import csv
import json
import logging
import multiprocessing
import os
import sys

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import ConnectionType, ApiKeyCredentials, AgentVersionObject
from azure.identity.aio import DefaultAzureCredential
from azure.core.credentials_async import AsyncTokenCredential
from azure.ai.projects.models import AgentReference, PromptAgentDefinition
from azure.ai.projects.models import FileSearchTool, AzureAISearchAgentTool, Tool, AgentVersionObject, AzureAISearchToolResource, AISearchIndexResource

from azure.ai.projects.models import (
    PromptAgentDefinition,
    EvaluationRule,
    ContinuousEvaluationRuleAction,
    EvaluationRuleFilter,
    EvaluationRuleEventType,
    EvaluatorCategory,
    EvaluatorDefinitionType
)


from openai import AsyncOpenAI
from dotenv import load_dotenv

from logging_config import configure_logging

load_dotenv()

logger = configure_logging(os.getenv("APP_LOG_FILE", ""))


def list_files_in_files_directory() -> List[str]:    
    # Get the absolute path of the 'files' directory
    files_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), 'files'))
    
    # List all files in the 'files' directory
    files = [f for f in os.listdir(files_directory) if os.path.isfile(os.path.join(files_directory, f))]
    
    return files

FILES_NAMES = list_files_in_files_directory()


async def create_index_maybe(
        ai_client: AIProjectClient, creds: AsyncTokenCredential) -> None:
    """
    Create the index and upload documents if the index does not exist.

    This code is executed only once, when called on_starting hook is being
    called. This code ensures that the index is being populated only once.
    rag.create_index return True if the index was created, meaning that this
    docker node have started first and must populate index.

    :param ai_client: The project client to be used to create an index.
    :param creds: The credentials, used for the index.
    """
    from api.search_index_manager import SearchIndexManager
    endpoint = os.environ.get('AZURE_AI_SEARCH_ENDPOINT')
    embedding = os.getenv('AZURE_AI_EMBED_DEPLOYMENT_NAME')    
    if endpoint and embedding:
        try:
            aoai_connection = await ai_client.connections.get_default(
                connection_type=ConnectionType.AZURE_OPEN_AI, include_credentials=True)
        except ValueError as e:
            logger.error("Error creating index: {e}")
            return
        
        embed_api_key = None
        if aoai_connection.credentials and isinstance(aoai_connection.credentials, ApiKeyCredentials):
            embed_api_key = aoai_connection.credentials.api_key

        search_mgr = SearchIndexManager(
            endpoint=endpoint,
            credential=creds,
            index_name=os.getenv('AZURE_AI_SEARCH_INDEX_NAME'),
            dimensions=None,
            model=embedding,
            deployment_name=embedding,
            embedding_endpoint=aoai_connection.target,
            embed_api_key=embed_api_key
        )
        # If another application instance already have created the index,
        # do not upload the documents.
        if await search_mgr.create_index(
            vector_index_dimensions=int(
                os.getenv('AZURE_AI_EMBED_DIMENSIONS'))):
            embeddings_path = os.path.join(
                os.path.dirname(__file__), 'data', 'embeddings.csv')

            assert embeddings_path, f'File {embeddings_path} not found.'
            await search_mgr.upload_documents(embeddings_path)
            await search_mgr.close()


def _get_file_path(file_name: str) -> str:
    """
    Get absolute file path.

    :param file_name: The file name.
    """
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__),
                     'files',
                     file_name))


async def get_available_tool(
        project_client: AIProjectClient,
        openai_client: AsyncOpenAI,
        creds: AsyncTokenCredential) -> Tool:
    """
    Get the toolset and tool definition for the agent.

    :param ai_client: The project client to be used to create an index.
    :param creds: The credentials, used for the index.
    :return: The tool set, available based on the environment.
    """
    # First try to get an index search.
    conn_id = os.environ.get('SEARCH_CONNECTION_ID')
    search_index_name = os.environ.get('AZURE_AI_SEARCH_INDEX_NAME')
    if search_index_name and conn_id:
        await create_index_maybe(project_client, creds)

        return AzureAISearchAgentTool(
            azure_ai_search=AzureAISearchToolResource(indexes=[AISearchIndexResource( 
                project_connection_id=conn_id,
                index_name=search_index_name,
                query_type="simple"
            )])
        )
    else:
        logger.info(
            "agent: index was not initialized, falling back to file search.")
        
        # Upload files for file search
        file_streams = [open(_get_file_path(file_name), "rb") for file_name in FILES_NAMES]

        try:
            vector_store = await openai_client.vector_stores.create()
            await openai_client.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store.id, files=file_streams
            )
            print(f"File uploaded to vector store (id: {vector_store.id})")
        except FileNotFoundError:
            print(f"Warning: Asset file not found.")
            print("Creating vector store without file for demonstration...")


        logger.info("agent: file store and vector store success")

        return FileSearchTool(vector_store_ids=[vector_store.id])


async def create_agent(ai_project: AIProjectClient,
                       creds: AsyncTokenCredential) -> AgentVersionObject:
    logger.info("Creating new agent with resources")
    tool = await get_available_tool(ai_project, await ai_project.get_openai_client(), creds)
    
    instructions = "Use AI Search always. Avoid to use base knowledge." if isinstance(tool, AzureAISearchAgentTool) else "Use File Search always.  Avoid to use base knowledge."

    agent = await ai_project.agents.create_version(
        agent_name=os.environ["AZURE_AI_AGENT_NAME"],
        definition=PromptAgentDefinition(
            model=os.environ["AZURE_AI_AGENT_DEPLOYMENT_NAME"],
            instructions=instructions,
            tools=[tool],
        ),
    )
    return agent

async def initialize_eval(project_client: AIProjectClient, agent: AgentVersionObject):
    print("Creating a single evaluator version - Prompt based (json style)")
    prompt_evaluator = await project_client.evaluators.create_version(
        name="my_custom_evaluator_prompt",
        evaluator_version={
            "name": "my_custom_evaluator_prompt",
            "categories": [EvaluatorCategory.QUALITY],
            "display_name": "my_custom_evaluator_prompt",
            "description": "Custom evaluator to for groundedness",
            "definition": {
                "type": EvaluatorDefinitionType.PROMPT,
                "prompt_text": """
                        You are a Groundedness Evaluator.

                        Your task is to evaluate how well the given response is grounded in the provided ground truth.
                        Groundedness means the response's statements are factually supported by the ground truth.
                        Evaluate factual alignment only — ignore grammar, fluency, or completeness.

                        ---

                        ### Input:
                        Query:
                        {query}

                        Response:
                        {response}

                        Ground Truth:
                        {ground_truth}

                        ---

                        ### Scoring Scale (1-5):
                        5 → Fully grounded. All claims supported by ground truth.  
                        4 → Mostly grounded. Minor unsupported details.  
                        3 → Partially grounded. About half the claims supported.  
                        2 → Mostly ungrounded. Only a few details supported.  
                        1 → Not grounded. Almost all information unsupported.

                        ---

                        ### Output should be Integer:
                        <integer from 1 to 5>
                """,
                "init_parameters": {
                    "type": "object",
                    "properties": {"deployment_name": {"type": "string"}, "threshold": {"type": "number"}},
                    "required": ["deployment_name"],
                },
                "data_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "response": {"type": "string"},
                        "ground_truth": {"type": "string"},
                    },
                    "required": ["query", "response", "ground_truth"],
                },
                "metrics": {
                    "tool_selection": {
                        "type": "ordinal",
                        "desirable_direction": "increase",
                        "min_value": 1,
                        "max_value": 5,
                    }
                },
            },
        },
    )

    print(f"Evaluator version created (id: {prompt_evaluator.id}, name: {prompt_evaluator.name})")

    print("Creating continuous evaluation rule to run evaluator on agent responses")
    continuous_eval_rule = await project_client.evaluation_rules.create_or_update(
        id="my-continuous-eval-rule",
        evaluation_rule=EvaluationRule(
            display_name="My Continuous Eval Rule",
            description="An eval rule that runs on agent response completions",
            action=ContinuousEvaluationRuleAction(eval_id=prompt_evaluator.id, max_hourly_runs=10),
            event_type=EvaluationRuleEventType.RESPONSE_COMPLETED,
            filter=EvaluationRuleFilter(agent_name=agent.name),
            enabled=True,
        ),
    )
    print(
        f"Continuous Evaluation Rule created (id: {continuous_eval_rule.id}, name: {continuous_eval_rule.display_name})"
    )



async def initialize_resources():
    proj_endpoint = os.environ.get("AZURE_EXISTING_AIPROJECT_ENDPOINT")
    try:
        async with DefaultAzureCredential() as credential:
            async with AIProjectClient(
                credential=credential,
                endpoint=proj_endpoint,
                api_version="2025-11-15-preview",
            ) as ai_project:
                # If the environment already has AZURE_AI_AGENT_ID or AZURE_EXISTING_AGENT_ID, try
                # fetching that agent
                agent_obj: Optional[AgentVersionObject] = None

                agentID = os.environ.get("AZURE_EXISTING_AGENT_ID")

                if agentID:
                    try:
                        agent_name = agentID.split(":")[0]
                        agent_version = agentID.split(":")[1]
                        agent_obj = await ai_project.agents.get_version(agent_name, agent_version)
                        logger.info(f"Found agent by ID: {agent_obj.id}")
                    except Exception as e:
                        logger.warning(
                            "Could not retrieve agent by AZURE_EXISTING_AGENT_ID = "
                            f"{agentID}, error: {e}")
                else:
                    logger.info("No existing agent ID found.")

                # Check if an agent with the same name already exists
                if not agent_obj:
                    try:
                        agent_name = os.environ["AZURE_AI_AGENT_NAME"]
                        logger.info(f"Retrieving agent by name: {agent_name}")
                        agents = await ai_project.agents.get(agent_name)
                        agent_obj = agents.versions.latest
                        logger.info(f"Agent with agent id, {agent_obj.id} retrieved.")
                    except Exception as e:
                        logger.info(f"Agent name, {agent_name} not found.")
                        
                # Create a new agent
                if not agent_obj:
                    agent_obj = await create_agent(ai_project, credential)
                    logger.info(f"Created agent, agent ID: {agent_obj.id}")

                os.environ["AZURE_EXISTING_AGENT_ID"] = agent_obj.id

                await initialize_eval(ai_project, agent_obj)                

    except Exception as e:
        logger.info("Error creating agent: {e}", exc_info=True)
        raise RuntimeError(f"Failed to create the agent: {e}")


def on_starting(server):
    """This code runs once before the workers will start."""
    asyncio.get_event_loop().run_until_complete(initialize_resources())


max_requests = 1000
max_requests_jitter = 50
log_file = "-"
bind = "0.0.0.0:50505"

if not os.getenv("RUNNING_IN_PRODUCTION"):
    reload = True

# Load application code before the worker processes are forked.
# Needed to execute on_starting.
# Please see the documentation on gunicorn
# https://docs.gunicorn.org/en/stable/settings.html
preload_app = True
num_cpus = multiprocessing.cpu_count()
workers = (num_cpus * 2) + 1
worker_class = "uvicorn.workers.UvicornWorker"

timeout = 120

if __name__ == "__main__":
    print("Running initialize_resources directly...")
    asyncio.run(initialize_resources())
    print("initialize_resources finished.")