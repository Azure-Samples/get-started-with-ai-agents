# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

import os
from pprint import pprint
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient

env_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/.env"))
load_dotenv(env_file)

def retrieve_agent(project_client: AIProjectClient):
    agent_id = os.environ.get("AZURE_EXISTING_AGENT_ID", "")
    agent_name =  os.environ.get("AZURE_AI_AGENT_NAME", "")
    agent_version = ""

    if not agent_name and (not agent_id or ":" not in agent_id):
        raise ValueError("Please set AZURE_EXISTING_AGENT_ID environment variable in the format 'agent_name:agent_version'.")

    if agent_id:
        agent_name = agent_id.split(":")[0]
        agent_version = agent_id.split(":")[1]


    if agent_version:
        agent = project_client.agents.get_version(
            agent_name=agent_name, agent_version=agent_version
        )
        print(f"Agent retrieved (id: {agent.id}, name: {agent.name}, version: {agent.version})")
    else:
        agent_obj = project_client.agents.get(agent_name=agent_name)
        agent = agent_obj.versions.latest
        print(f"Latest agent version retrieved (id: {agent.id}, name: {agent.name}, version: {agent.version})")

    return agent

def retrieve_endpoint():
    endpoint = os.environ.get("AZURE_EXISTING_AIPROJECT_ENDPOINT", "")
    if not endpoint:
        raise ValueError("Please set AZURE_EXISTING_AIPROJECT_ENDPOINT environment variable.")
    return endpoint

def retrieve_model_deployment():
    deployment = os.environ.get("AZURE_AI_AGENT_DEPLOYMENT_NAME", "")
    if not deployment:
        raise ValueError("Please set AZURE_AI_AGENT_DEPLOYMENT_NAME environment variable.")
    return deployment

class Colors:
    RED = "\033[91m"
    GREEN = '\033[92m'    
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
    
    @staticmethod
    def reset():
        """Properly reset terminal colors"""
        print("\033[0m", end='', flush=True)