# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

from typing import cast
import os
import time
from pathlib import Path
from dotenv import load_dotenv

from azure.identity import DefaultAzureCredential
from azure.ai.evaluation.red_team import RedTeam, RiskCategory, AttackStrategy
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import AgentVersionObject
from openai.types.responses import Response

async def run_red_team():
    # Load environment variables from .env file
    current_dir = Path(__file__).parent
    env_path = current_dir / "../src/.env"
    load_dotenv(dotenv_path=env_path)
    
    credential = DefaultAzureCredential()

    project_endpoint = os.environ.get("AZURE_EXISTING_AIPROJECT_ENDPOINT")
        
    # Validate required environment variables
    if not project_endpoint:
        raise ValueError("Please set the AZURE_EXISTING_AIPROJECT_ENDPOINT environment variable.")
        
    with DefaultAzureCredential(exclude_interactive_browser_credential=False) as credential:
        with AIProjectClient(endpoint=project_endpoint, credential=credential) as project_client:

            # Deterime agent name and version
            agent_id = os.environ.get("AZURE_EXISTING_AGENT_ID")
            agent_name = os.environ.get("AZURE_AI_AGENT_NAME", "")
            agent_version = ""
            if agent_id:
                if len(agent_id.strip(":")) != 2:
                    raise ValueError("AZURE_EXISTING_AGENT_ID should be in the format 'agent_name:agent_version' if provided.")
                agent_version_obj = cast(AgentVersionObject, project_client.agents.retrieve_version(agent_name=agent_id.split(":")[0], version=agent_id.split(":")[1]))
                agent_version = agent_version_obj.version
            elif agent_name:
                agent_version_obj = project_client.agents.retrieve(agent_name=agent_name).versions.latest
                agent_version = agent_version_obj.version
            else:
                raise ValueError("Please set either AZURE_EXISTING_AGENT_ID or AZURE_AI_AGENT_NAME environment variable.")
        
            openai_client = project_client.get_openai_client()


            conversation = openai_client.conversations.create()

            def agent_callback(query: str) -> str:
                response: Response = openai_client.responses.create(input=query, conversation_id=conversation.id, extra_body={"agent": {"name": agent_name, "version": agent_version, "type": "agent_reference"}},)
                return response.output_text

            # Print agent details to verify correct targeting
            print(f"Running Red Team evaluation against agent:")
            print(f"  - Agent ID: {agent_name}:{agent_version}")
            print(f"  - Agent Name: {agent_name}")
            print(f"  - Agent Version: {agent_version}")
            print(f"  - Using Model: {getattr(agent_version_obj.definition, 'model', '')}")
            
            red_team = RedTeam(
                azure_ai_project=project_endpoint,
                credential=credential,
                risk_categories=[RiskCategory.Violence],
                num_objectives=1,
                output_dir="redteam_outputs/"
            )

            print("Starting Red Team scan...")
            await red_team.scan(
                target=agent_callback,
                scan_name="Agent-Scan",
                attack_strategies=[AttackStrategy.Flip],
            )
            print("Red Team scan complete.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_red_team())