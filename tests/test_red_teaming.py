# pylint: disable=line-too-long,useless-suppression
# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

from pprint import pprint
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    AgentVersionObject,
    EvaluationTaxonomy,
    AzureAIAgentTarget,
    AgentTaxonomyInput,
    RiskCategory,
)
import time
from azure.ai.projects.models import EvaluationTaxonomy, AgentVersionObject
from test_utils import retrieve_agent, retrieve_endpoint

def test_red_teaming() -> None:

    with (
        DefaultAzureCredential(exclude_interactive_browser_credential=False) as credential,
        AIProjectClient(endpoint=retrieve_endpoint(), credential=credential) as project_client,
        project_client.get_openai_client() as client,
    ):
            
        agent = retrieve_agent(project_client)

        eval_group_name = "Red Team Agent Safety evaluation -" + str(int(time.time()))
        eval_run_name = f"Red Team Agent Safety evaluation run for {agent.name} -" + str(int(time.time()))
        data_source_config = {"type": "azure_ai_source", "scenario": "red_team"}

        # Define testing criteria for red teaming. 
        # Explore evaluator catalog for assessments of additional risk categories.
        testing_criteria = [
             {
                "type": "azure_ai_evaluator",
                "name": "Prohibited Actions",
                "evaluator_name": "builtin.prohibited_actions"
            }
        ]
        pprint(testing_criteria)

        eval_object = client.evals.create(
            name=eval_group_name,
            data_source_config=data_source_config,
            testing_criteria=testing_criteria,
        )
        print(f"Red team evaluation created for red teaming: {eval_group_name}")

        risk_categories_for_taxonomy = [RiskCategory.PROHIBITED_ACTIONS]
        target = AzureAIAgentTarget(
            name=agent.name, version=agent.version, tool_descriptions=_get_tool_descriptions(agent)
        )
        agent_taxonomy_input = AgentTaxonomyInput(risk_categories=risk_categories_for_taxonomy, target=target)
        eval_taxonomy_input = EvaluationTaxonomy(
            description="Taxonomy for red teaming evaluation", taxonomy_input=agent_taxonomy_input
        )
        taxonomy = project_client.evaluation_taxonomies.create(name=agent.name, body=eval_taxonomy_input)
        
        # Submit evaluation run for red teaming
        eval_run_object = client.evals.runs.create(
            eval_id=eval_object.id,
            name=eval_run_name,
            data_source={
                "type": "azure_ai_red_team",
                "item_generation_params": {
                    "type": "red_team_taxonomy",
                    "attack_strategies": ["Flip", "Base64"],
                    "num_turns": 1, # number of interaction turns per item
                    "source": {"type": "file_id", "id": taxonomy.id},
                },
                "target": target.as_dict(),
            },
        )

        print(f"Eval Run created for red teaming: {eval_run_name}")
        
        # Poll for completion
        while True:
            run = client.evals.runs.retrieve(run_id=eval_run_object.id, eval_id=eval_object.id)
            if run.status == "completed" or run.status == "failed":
                print(f"Result Counts: {run.result_counts}")
                print(f"Report URL: {run.report_url}")
                break
            time.sleep(5)
            print(f"Waiting for eval run to complete... {run.status}")

        # assertions
        assert run.status == "completed", "Evaluation run did not complete successfully. Review logs from the evaluation report."
        assert run.result_counts.errored == 0, "There were errored evaluation items. Review error details in the evaluation report."
        assert run.result_counts.failed == 0, "There were failed evaluation items. Review evaluation results and explanations in the evaluation report."


def _get_tool_descriptions(agent: AgentVersionObject):
    tools = agent.definition.get("tools", [])
    tool_descriptions = []
    for tool in tools:
        if tool["type"] == "openapi":
            tool_descriptions.append(
                {
                    "name": tool["openapi"]["name"],
                    "description": (
                        tool["openapi"]["description"]
                        if "description" in tool["openapi"]
                        else "No description provided"
                    ),
                }
            )
        else:
            tool_descriptions.append(
                {
                    "name": tool["name"] if "name" in tool else "Unnamed Tool",
                    "description": tool["description"] if "description" in tool else "No description provided",
                }
            )

    return tool_descriptions