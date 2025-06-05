# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license.
# See LICENSE file in the project root for full license information.
from typing import Dict, List

import asyncio
import csv
import json
import logging
import multiprocessing
import os
import sys

from azure.ai.projects.aio import AIProjectClient
from azure.ai.agents.models import (
    Agent,
    AsyncToolSet,
    AzureAISearchTool,
    FilePurpose,
    FileSearchTool,
    Tool,
)
from azure.ai.projects.models import ConnectionType
from azure.identity.aio import DefaultAzureCredential
from azure.core.credentials_async import AsyncTokenCredential

from dotenv import load_dotenv

from logging_config import configure_logging

load_dotenv()

logger = configure_logging(os.getenv("APP_LOG_FILE", ""))


agentID = os.environ.get("AZURE_EXISTING_AGENT_ID") if os.environ.get(
    "AZURE_EXISTING_AGENT_ID") else os.environ.get(
        "AZURE_AI_AGENT_ID")
    
proj_endpoint = os.environ.get("AZURE_EXISTING_AIPROJECT_ENDPOINT")

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
        if aoai_connection.credentials is None or aoai_connection.credentials.api_key is None: 
            err = "Error getting the connection to Azure Open AI service. {}"
            if aoai_connection is not None and (aoai_connection.key is None or  aoai_connection.credentials.api_key is None):
                logger.error(
                    err.format(
                        "Please configure "
                        f"{aoai_connection.name} to use API key."))
            else:
                logger.error(
                    err.format("Azure Open AI service connection is absent."))
            return
        
        search_mgr = SearchIndexManager(
            endpoint=endpoint,
            credential=creds,
            index_name=os.getenv('AZURE_AI_SEARCH_INDEX_NAME'),
            dimensions=None,
            model=embedding,
            deployment_name=embedding,
            embedding_endpoint=aoai_connection.target,
            embed_api_key=aoai_connection.credentials.api_key
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
        creds: AsyncTokenCredential) -> Tool:
    """
    Get the toolset and tool definition for the agent.

    :param ai_client: The project client to be used to create an index.
    :param creds: The credentials, used for the index.
    :return: The tool set, available based on the environment.
    """
    # File name -> {"id": file_id, "path": file_path}
    file_ids: List[str] = []
    # First try to get an index search.
    conn_id = ""
    if os.environ.get('AZURE_AI_SEARCH_INDEX_NAME'):
        conn_list = project_client.connections.list()
        async for conn in conn_list:
            if conn.type == ConnectionType.AZURE_AI_SEARCH:
                conn_id = conn.id
                break

    toolset = AsyncToolSet()
    if conn_id:
        await create_index_maybe(project_client, creds)

        return AzureAISearchTool(
            index_connection_id=conn_id,
            index_name=os.environ.get('AZURE_AI_SEARCH_INDEX_NAME'))
    else:
        logger.info(
            "agent: index was not initialized, falling back to file search.")
        
        # Upload files for file search
        for file_name in FILES_NAMES:
            file_path = _get_file_path(file_name)
            file = await project_client.agents.files.upload_and_poll(
                file_path=file_path, purpose=FilePurpose.AGENTS)
            # Store both file id and the file path using the file name as key.
            file_ids.append(file.id)

        # Create the vector store using the file IDs.
        vector_store = await project_client.agents.vector_stores.create_and_poll(
            file_ids=file_ids,
            name="sample_store"
        )
        logger.info("agent: file store and vector store success")

        return FileSearchTool(vector_store_ids=[vector_store.id])


async def create_agent(ai_client: AIProjectClient,
                       creds: AsyncTokenCredential) -> Agent:
    logger.info("Creating new agent with resources")
    tool = await get_available_tool(ai_client, creds)
    toolset = AsyncToolSet()
    toolset.add(tool)
    
    instructions = "Use AI Search always. Avoid to use base knowledge." if isinstance(tool, AzureAISearchTool) else "Use File Search always.  Avoid to use base knowledge."
    
    agent = await ai_client.agents.create_agent(
        model=os.environ["AZURE_AI_AGENT_DEPLOYMENT_NAME"],
        name=os.environ["AZURE_AI_AGENT_NAME"],
        instructions=instructions,
        toolset=toolset
    )
    return agent


async def initialize_resources():
    try:
        async with DefaultAzureCredential(
                exclude_shared_token_cache_credential=True) as creds:
            async with AIProjectClient(
                credential=creds,
                endpoint=proj_endpoint
            ) as ai_client:
                # If the environment already has AZURE_AI_AGENT_ID or AZURE_EXISTING_AGENT_ID, try
                # fetching that agent
                if agentID is not None:
                    try:
                        agent = await ai_client.agents.get_agent(
                            agentID)
                        logger.info(f"Found agent by ID: {agent.id}")
                        return
                    except Exception as e:
                        logger.warning(
                            "Could not retrieve agent by AZURE_EXISTING_AGENT_ID = "
                            f"{agentID}, error: {e}")

                # Check if an agent with the same name already exists
                agent_list = ai_client.agents.list_agents()
                if agent_list:
                    async for agent_object in agent_list:
                        if agent_object.name == os.environ[
                                "AZURE_AI_AGENT_NAME"]:
                            logger.info(
                                "Found existing agent named "
                                f"'{agent_object.name}'"
                                f", ID: {agent_object.id}")
                            os.environ["AZURE_EXISTING_AGENT_ID"] = agent_object.id
                            return
                        
                # Create a new agent
                agent = await create_agent(ai_client, creds)
                os.environ["AZURE_EXISTING_AGENT_ID"] = agent.id
                logger.info(f"Created agent, agent ID: {agent.id}")

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