# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license.
# See LICENSE file in the project root for full license information.
from typing import Dict, List, Optional

import asyncio
import multiprocessing
import os
import tempfile

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import ConnectionType, ApiKeyCredentials, AgentVersionObject
from azure.identity.aio import DefaultAzureCredential
from azure.core.credentials_async import AsyncTokenCredential
from azure.ai.projects.models import PromptAgentDefinition
from azure.ai.projects.models import FileSearchTool, AzureAISearchAgentTool, Tool, AgentVersionObject, AzureAISearchToolResource, AISearchIndexResource
from azure.storage.blob.aio import BlobServiceClient

from azure.ai.projects.models import (
    PromptAgentDefinition,
    EvaluationRule,
    ContinuousEvaluationRuleAction,
    EvaluationRuleFilter,
    EvaluationRuleEventType,
    EvaluationRuleActionType
)


from openai import AsyncOpenAI
from dotenv import load_dotenv
from logging_config import configure_logging
from util import get_env_file_path

# Load environment variables from azd environment folder for local development
env_file = get_env_file_path()
load_dotenv(env_file)

logger = configure_logging(os.getenv("APP_LOG_FILE", ""))
if env_file:
    logger.info(f"Loaded environment variables from {env_file}")
else:
    logger.info("Loaded environment variables from default location")


import logging
import os


# Raise Azure SDK loggers to DEBUG
logging.getLogger("azure").setLevel(logging.DEBUG)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.DEBUG)

# If you want less noise from retry + transport:
logging.getLogger("azure.core.pipeline.policies.retry").setLevel(logging.INFO)
logging.getLogger("azure.core.pipeline.transport").setLevel(logging.INFO)



def list_files_in_files_directory() -> List[str]:    
    # Get the absolute path of the 'files' directory
    files_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), 'files'))
    
    # List all files in the 'files' directory
    files = [f for f in os.listdir(files_directory) if os.path.isfile(os.path.join(files_directory, f))]
    
    return files

FILES_NAMES = list_files_in_files_directory()


async def execute_step(
    step_name: str,
    step_func,
    resources: Dict,
    steps_order: List[str]
) -> None:
    """
    Execute a step and check that the prior step succeeded.
    
    :param step_name: Name of the step to execute
    :param step_func: Async function to execute for this step
    :param resources: Dictionary to track resource status
    :param steps_order: List of step names in execution order
    """
    from api.search_index_manager import ResourceStatus
    
    # Check if this step has a prior step
    step_index = steps_order.index(step_name)
    if step_index > 0:
        prior_step = steps_order[step_index - 1]
        prior_status = resources.get(prior_step)
        if prior_status == ResourceStatus.FAILED:
            logger.error(f"Skipping step '{step_name}' because prior step '{prior_step}' failed.")
            resources[step_name] = ResourceStatus.FAILED
            return
    
    # Execute the step
    try:
        status = await step_func()
        resources[step_name] = status
    except Exception as e:
        logger.error(f"Step '{step_name}' raised exception: {e}")
        resources[step_name] = ResourceStatus.FAILED


def _print_summary(resources: Dict, steps_order: List[str]) -> None:
    """
    Print a summary of all steps and their status.
    
    :param resources: Dictionary with step names and their ResourceStatus
    :param steps_order: List of step names in execution order
    """
    logger.info("=" * 80)
    logger.info("Azure AI Search Setup Summary")
    logger.info("=" * 80)
    
    for i, step_name in enumerate(steps_order, 1):
        status = resources.get(step_name)
        if status:
            status_symbol = "✓" if status.value == "created" else "ℹ" if status.value == "existing" else "✗"
            logger.info(f"{i}. {step_name}: {status_symbol} {status.value}")
        else:
            logger.info(f"{i}. {step_name}: ✗ failed")
    
    logger.info("=" * 80)


async def create_ai_search_tool_maybe(
        ai_client: AIProjectClient, creds: AsyncTokenCredential) -> Optional[Tool]:
    """
    Create AI Search tool with all required resources (index, datasource, skillset, indexers).
    Returns the tool only if all steps succeed.

    :param ai_client: The project client to be used to create resources.
    :param creds: The credentials, used for the resources.
    :return: AzureAISearchAgentTool if successful, None otherwise
    """
    from api.search_index_manager import SearchIndexManager, ResourceStatus
    from api.blob_store_manager import BlobStoreManager
    from openai import AsyncAzureOpenAI
    
    endpoint = os.environ.get('AZURE_AI_SEARCH_ENDPOINT')
    embedding = os.getenv('AZURE_AI_EMBED_DEPLOYMENT_NAME')
    container_name = os.getenv('AZURE_BLOB_CONTAINER_NAME', 'documents')
    search_index_name = os.getenv('AZURE_AI_SEARCH_INDEX_NAME', 'index-sample')
    
    if not endpoint or not embedding:
        logger.warning("AI Search endpoint or embedding deployment not configured. Skipping AI Search setup.")
        return None
    
    try:
        aoai_connection = await ai_client.connections.get_default(
            connection_type=ConnectionType.AZURE_OPEN_AI, include_credentials=True)
    except ValueError as e:
        logger.error(f"Failed to get Azure OpenAI connection: {e}")
        return None
    
    # Create embedding client with AAD authentication
    embedding_client = AsyncAzureOpenAI(
        api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'),
        azure_endpoint=aoai_connection.target,
        azure_ad_token_provider=creds.get_token
    )

    # Initialize SearchIndexManager
    search_mgr = SearchIndexManager(
        endpoint=endpoint,
        credential=creds,
        index_name=search_index_name,
        dimensions=int(os.getenv('AZURE_AI_EMBED_DIMENSIONS', '1536')),
        model=embedding,
        deployment_name=embedding,
        embedding_endpoint=aoai_connection.target,
        embed_api_key=None,
        embedding_client=embedding_client
    )
    
    # Get blob storage connection
    try:
        storage_connection = await ai_client.connections.get_default(
            connection_type=ConnectionType.AZURE_STORAGE_ACCOUNT,
            include_credentials=True)
        storage_account_endpoint = storage_connection.target
    except ValueError as e:
        logger.error(f"Failed to get Blob Storage connection: {e}")
        return None
    
    # Get connection string from STORAGE_ACCOUNT_RESOURCE_ID
    storage_account_resource_id = os.getenv("STORAGE_ACCOUNT_RESOURCE_ID")
    if not storage_account_resource_id:
        logger.error("Missing required environment variable: STORAGE_ACCOUNT_RESOURCE_ID")
        return None
    
    connection_string = f"ResourceId={storage_account_resource_id};"
    
    # Sanitize index name for resource naming
    sanitized_name = search_index_name.lower().replace("_", "-")
    datasource_name = f"{sanitized_name}-datasource"
    skillset_name = f"{sanitized_name}-skillset"
    
    # Define steps in execution order
    steps_order = [
        "blob_container",
        "blob_upload",
        "search_index",
        "search_datasource",
        "search_skillset",
        "indexer_json",
        "indexer_markdown",
        "indexer_documents",
    ]
    
    resources = {}
    
    # Step 1: Create blob container
    async def blob_container_step():
        blob_mgr = BlobStoreManager(
            account_url=storage_account_endpoint,
            credential=creds
        )
        return await blob_mgr.create_blob_container_maybe(container_name)
    
    await execute_step("blob_container", blob_container_step, resources, steps_order)
    
    # Step 2: Upload files to blob
    async def blob_upload_step():
        blob_mgr = BlobStoreManager(
            account_url=storage_account_endpoint,
            credential=creds
        )
        files_dir = os.path.join(os.path.dirname(__file__), 'files')
        return await blob_mgr.upload_to_blob_store_maybe(container_name, files_dir)
    
    await execute_step("blob_upload", blob_upload_step, resources, steps_order)
    
    # Step 3: Create search index
    async def search_index_step():
        return await search_mgr.create_index_maybe(
            vector_index_dimensions=int(os.getenv('AZURE_AI_EMBED_DIMENSIONS', '1536'))
        )
    
    await execute_step("search_index", search_index_step, resources, steps_order)
    
    # Step 4: Create datasource
    async def datasource_step():
        return await search_mgr.create_datasource_maybe(
            datasource_name=datasource_name,
            container_name=container_name,
            connection_string=connection_string
        )
    
    await execute_step("search_datasource", datasource_step, resources, steps_order)
    
    # Step 5: Create skillset
    async def skillset_step():
        return await search_mgr.create_skillset_maybe(
            skillset_name=skillset_name,
            target_index_name=search_index_name
        )
    
    await execute_step("search_skillset", skillset_step, resources, steps_order)
    
    # Step 6: Create JSON indexer
    async def json_indexer_step():
        return await search_mgr.create_indexer_maybe(
            indexer_name=f"{sanitized_name}-json-indexer",
            datasource_name=datasource_name,
            target_index_name=search_index_name,
            skillset_name=skillset_name,
            file_extensions=".json",
            parsing_mode="json"
        )
    
    await execute_step("indexer_json", json_indexer_step, resources, steps_order)
    
    # Step 7: Create Markdown indexer
    async def markdown_indexer_step():
        return await search_mgr.create_indexer_maybe(
            indexer_name=f"{sanitized_name}-markdown-indexer",
            datasource_name=datasource_name,
            target_index_name=search_index_name,
            skillset_name=skillset_name,
            file_extensions=".md",
            parsing_mode="markdown"
        )
    
    await execute_step("indexer_markdown", markdown_indexer_step, resources, steps_order)
    
    # Step 8: Create Documents indexer
    async def documents_indexer_step():
        return await search_mgr.create_indexer_maybe(
            indexer_name=f"{sanitized_name}-documents-indexer",
            datasource_name=datasource_name,
            target_index_name=search_index_name,
            skillset_name=skillset_name,
            file_extensions=".pdf,.docx,.pptx,.xlsx,.txt",
            parsing_mode="default"
        )
    
    await execute_step("indexer_documents", documents_indexer_step, resources, steps_order)
    
    # Check if all steps succeeded
    all_succeeded = all(s != ResourceStatus.FAILED for s in resources.values())
    
    # Print summary
    _print_summary(resources, steps_order)
    
    # Return tool only if all steps succeeded
    if all_succeeded:
        logger.info("✓ All AI Search resources created/configured successfully!")
        conn_id = os.environ.get('SEARCH_CONNECTION_ID')
        if conn_id:
            return AzureAISearchAgentTool(
                azure_ai_search=AzureAISearchToolResource(indexes=[AISearchIndexResource(
                    project_connection_id=conn_id,
                    index_name=search_index_name,
                    query_type="simple"
                )])
            )
    else:
        logger.error("✗ Some AI Search resources failed to create/configure. Falling back to File Search.")
        return None


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
        creds: AsyncTokenCredential) -> Optional[Tool]:
    """
    Get the toolset and tool definition for the agent.

    :param project_client: The project client to be used to create an index.
    :param openai_client: The OpenAI client.
    :param creds: The credentials, used for the index.
    :return: AzureAISearchAgentTool if AI Search enabled and succeeds, 
             FileSearchTool if File Search is used, or None if both fail.
    """
    use_ai_search = os.environ.get('USE_AZURE_AI_SEARCH_SERVICE', 'false').lower() == 'true'
    conn_id = os.environ.get('SEARCH_CONNECTION_ID')
    search_index_name = os.environ.get('AZURE_AI_SEARCH_INDEX_NAME')
    
    # If AI Search is explicitly required
    if use_ai_search:
        if not search_index_name or not conn_id:
            logger.warning(
                "USE_AZURE_AI_SEARCH_SERVICE is set to 'true' but required environment variables are missing. "
                "Please ensure SEARCH_CONNECTION_ID and AZURE_AI_SEARCH_INDEX_NAME are configured. "
                "Creating agent without search tool."
            )
            return None
        
        logger.info("AI Search is required. Attempting to create AI Search tool...")
        ai_search_tool = await create_ai_search_tool_maybe(project_client, creds)
        
        if ai_search_tool:
            return ai_search_tool
        else:
            logger.warning(
                "AI Search initialization failed. "
                "Please check the logs above for details on which step failed. "
                "Creating agent without search tool."
            )
            return None
    
    # If AI Search is not required, use File Search
    logger.info("AI Search is not enabled. Using File Search tool.")
    
    # Upload files for file search
    file_streams = [open(_get_file_path(file_name), "rb") for file_name in FILES_NAMES]

    try:
        vector_store = await openai_client.vector_stores.create()
        await openai_client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id, files=file_streams
        )
        logger.info(f"Files uploaded to vector store (id: {vector_store.id})")
        logger.info("File Search tool ready")
        return FileSearchTool(vector_store_ids=[vector_store.id])
    except FileNotFoundError:
        logger.warning(f"Asset file not found.")
        logger.error("Failed to initialize File Search tool due to missing files.")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize File Search tool: {e}")
        return None


async def create_agent(ai_project: AIProjectClient,
                       openai_client: AsyncOpenAI,
                       creds: AsyncTokenCredential) -> AgentVersionObject:
    logger.info("Creating new agent with resources")
    tool = await get_available_tool(ai_project, openai_client, creds)

    instructions = "You are a helpful assistant."
    tools = []
    
    if tool is not None:
        tools = [tool]
        if isinstance(tool, AzureAISearchAgentTool):
            instructions = (
                "Use AI Search always. "
                "You must always provide citations for answers using the tool and render them as: `\u3010message_idx:search_idx\u2020source\u3011`. "
                "Avoid to use base knowledge."
            )
        else:
            instructions = "Use File Search always with citations. Avoid to use base knowledge."
    else:
        logger.warning("No search tool available. Creating agent without search tool.")

    agent = await ai_project.agents.create_version(
        agent_name=os.environ["AZURE_AI_AGENT_NAME"],
        definition=PromptAgentDefinition(
            model=os.environ["AZURE_AI_AGENT_DEPLOYMENT_NAME"],
            instructions=instructions,
            tools=tools,
        ),
    )
    return agent


async def initialize_eval(project_client: AIProjectClient, openai_client: AsyncOpenAI, agent_obj: AgentVersionObject, credential: AsyncTokenCredential):
    eval_rule_id = f"eval-rule-for-{agent_obj.name}"
    try:
        eval_rules = project_client.evaluation_rules.list(
            action_type=EvaluationRuleActionType.CONTINUOUS_EVALUATION,
            agent_name=agent_obj.name)
        rules_list = [rule async for rule in eval_rules]

        if len(rules_list) >= 1:
            logger.info(f"Continuous Evaluation Rule for agent {agent_obj.name} already exists")
        else:
            # Create an evaluation with testing criteria
            data_source_config = {"type": "azure_ai_source", "scenario": "responses"}
            testing_criteria = [
                {   "type": "azure_ai_evaluator", 
                    "name": "violence",
                    "evaluator_name": "builtin.violence",
                    "initialization_parameters": {"deployment_name": os.environ["AZURE_AI_AGENT_DEPLOYMENT_NAME"]},
                }
            ]
            eval_object = await openai_client.evals.create(
                name=f"{agent_obj.name} Continuous Evaluation",
                data_source_config=data_source_config,  # type: ignore
                testing_criteria=testing_criteria,  # type: ignore
            )
            logger.info(f"Evaluation created (id: {eval_object.id}, name: {eval_object.name})")

            # Configure a rule that triggers the evaluation on agent responses
            continuous_eval_rule = await project_client.evaluation_rules.create_or_update(
                id=eval_rule_id,
                evaluation_rule=EvaluationRule(
                    display_name=f"{agent_obj.name} Continuous Eval Rule",
                    description="An eval rule that runs on agent response completions",
                    action=ContinuousEvaluationRuleAction(
                        eval_id=eval_object.id, # link to evaluation created above
                        max_hourly_runs=5), # set max eval run limit per hour
                    event_type=EvaluationRuleEventType.RESPONSE_COMPLETED,
                    filter=EvaluationRuleFilter(agent_name=agent_obj.name),
                    enabled=True,
                ),
            )
            logger.info(
                f"Continuous Evaluation Rule created (id: {continuous_eval_rule.id}, name: {continuous_eval_rule.display_name})"
            )
    except Exception as e:
        logger.error(f"Error creating Continuous Evaluation Rule: {e}", exc_info=True)

async def initialize_resources():
    proj_endpoint = os.environ.get("AZURE_EXISTING_AIPROJECT_ENDPOINT")
    try:
        async with (
            DefaultAzureCredential() as credential,
            AIProjectClient(endpoint=proj_endpoint, credential=credential) as project_client,
            project_client.get_openai_client() as openai_client,
        ):
            agent_obj: Optional[AgentVersionObject] = None

            agentID = os.environ.get("AZURE_EXISTING_AGENT_ID")

            if agentID:
                try:
                    agent_name = agentID.split(":")[0]
                    agent_version = agentID.split(":")[1]
                    agent_obj = await project_client.agents.get_version(agent_name, agent_version)
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
                    agents = await project_client.agents.get(agent_name)
                    agent_obj = agents.versions.latest
                    logger.info(f"Agent with agent id, {agent_obj.id} retrieved.")
                except Exception as e:
                    logger.info(f"Agent name, {agent_name} not found.")
                    
            # Create a new agent
            if not agent_obj:
                agent_obj = await create_agent(project_client, openai_client, credential)
                logger.info(f"Created agent, agent ID: {agent_obj.id}")

            os.environ["AZURE_EXISTING_AGENT_ID"] = agent_obj.id

            # await initialize_eval(project_client, openai_client, agent_obj, credential)
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
    logger.info("Running initialize_resources directly...")
    asyncio.run(initialize_resources())
    logger.info("initialize_resources finished.")