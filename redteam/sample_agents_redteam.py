# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

"""
DESCRIPTION:
    This sample demonstrates how to use basic agent operations from
    the Azure Agents service using a synchronous client.

USAGE:
    python sample_agents_redteam.py

    Before running the sample:

    pip install azure-ai-agents azure-ai-projects azure-identity azure-ai-evaluation[redteam]

    Set these environment variables with your own values:
    1) PROJECT_ENDPOINT - The Azure AI Project endpoint, as found in the Overview 
                          page of your Azure AI Foundry portal.
    2) MODEL_DEPLOYMENT_NAME - The deployment name of the AI model, as found under the "Name" column in 
       the "Models + endpoints" tab in your Azure AI Foundry project.
    3) AGENT_ID - The ID of the agent you want to use, as found in the "Agents" tab of your Azure AI Foundry project.
"""


from typing import Optional, Dict, Any
import os
import time

# Azure imports
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.ai.evaluation.red_team import RedTeam, RiskCategory, AttackStrategy
from azure.ai.projects import AIProjectClient
import azure.ai.agents
from azure.ai.agents.models import ListSortOrder

async def run_red_team():
    # Initialize Azure credentials
    credential = DefaultAzureCredential()

    endpoint = os.environ["PROJECT_ENDPOINT"]
    model_deployment_name = os.environ["MODEL_DEPLOYMENT_NAME"]
    agent_id = os.environ["AGENT_ID"]

    with DefaultAzureCredential(exclude_interactive_browser_credential=False) as credential:
        with AIProjectClient(endpoint=endpoint, credential=credential) as project_client:
            agent = project_client.agents.get_agent(agent_id)
            thread = project_client.agents.threads.create()

            def agent_callback(query: str) -> str:
                message = project_client.agents.messages.create(thread_id=thread.id, role="user", content=query)
                run = project_client.agents.runs.create(thread_id=thread.id, agent_id=agent.id)

                # Poll the run as long as run status is queued or in progress
                while run.status in ["queued", "in_progress", "requires_action"]:
                    # Wait for a second
                    time.sleep(1)
                    run = project_client.agents.runs.get(thread_id=thread.id, run_id=run.id)
                    # [END create_run]
                    print(f"Run status: {run.status}")

                if run.status == "failed":
                    print(f"Run error: {run.last_error}")
                    return "Error: Agent run failed."
                messages = project_client.agents.messages.list(thread_id=thread.id, order=ListSortOrder.DESCENDING)
                for msg in messages:
                    if msg.text_messages:
                        return msg.text_messages[0].text.value
                return "Could not get a response from the agent."
        

            red_team = RedTeam(
                azure_ai_project=endpoint,
                credential=credential,
                risk_categories=[RiskCategory.Violence],
                num_objectives=1,
                output_dir="redteam_outputs/"
            )

            result = await red_team.scan(
                target=agent_callback,
                scan_name="Agent-Scan",
                attack_strategies=[AttackStrategy.Flip],
            )

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_red_team())