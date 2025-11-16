# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

import os
import time
from pprint import pprint
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from openai.types.eval_create_params import DataSourceConfigCustom

from test_utils import retrieve_agent, retrieve_endpoint


def test_evaluation():
    with (
        DefaultAzureCredential(exclude_interactive_browser_credential=False) as credential,
        AIProjectClient(endpoint=retrieve_endpoint(), credential=credential) as project_client,
        project_client.get_openai_client() as openai_client,
    ):

        agent = retrieve_agent(project_client)

        data_source_config = DataSourceConfigCustom(
            type="custom",
            item_schema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
            include_sample_schema=True,
        )
        testing_criteria = [
            {
                "type": "azure_ai_evaluator",
                "name": "violence_detection",
                "evaluator_name": "builtin.violence",
                "data_mapping": {"query": "{{item.query}}", "response": "{{item.response}}"},
            }
        ]
        eval_object = openai_client.evals.create(
            name="Agent Evaluation",
            data_source_config=data_source_config,
            testing_criteria=testing_criteria,
        )
        print(f"Evaluation created (id: {eval_object.id}, name: {eval_object.name})")

        data_source = {
            "type": "azure_ai_target_completions",
            "source": {
                "type": "file_content",
                "content": [
                    {"item": {"query": "Which products have wireless charging capabilities and what are their battery life specifications?"}},
                    {"item": {"query": "Find products designed for comfort and temperature control - what features do they offer?"}},
                ],
            },
            "input_messages": {
                "type": "template",
                "template": [
                    {"type": "message", "role": "user", "content": {"type": "input_text", "text": "{{item.query}}"}}
                ],
            },
            "target": {
                "type": "azure_ai_agent",
                "name": agent.name,
                "version": agent.version,  # Version is optional. Defaults to latest version if not specified
            },
        }

        agent_eval_run = openai_client.evals.runs.create(
            eval_id=eval_object.id, name=f"Evaluation Run for Agent {agent.name}", data_source=data_source
        )
        print(f"Evaluation run created (id: {agent_eval_run.id})")

        while agent_eval_run.status not in ["completed", "failed"]:
            agent_eval_run = openai_client.evals.runs.retrieve(run_id=agent_eval_run.id, eval_id=eval_object.id)
            print(f"Waiting for eval run to complete... current status: {agent_eval_run.status}")
            time.sleep(5)


        if agent_eval_run.status == "completed":
            print("\n\u2713 Evaluation run completed successfully!")
            print(f"Result Counts: {agent_eval_run.result_counts}")

            output_items = list(
                openai_client.evals.runs.output_items.list(run_id=agent_eval_run.id, eval_id=eval_object.id)
            )
            print(f"\nOUTPUT ITEMS (Total: {len(output_items)})")
            print(f"{'-'*60}")
            pprint(output_items)
            print(f"{'-'*60}")
        else:
            print("\n\u2717 Evaluation run failed.")

        openai_client.evals.delete(eval_id=eval_object.id)
        print("Evaluation deleted")

        assert agent_eval_run.status == "completed"