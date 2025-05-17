import os
import time
import json

from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urlparse

from azure.ai.agents.models import RunStatus, MessageRole
from azure.ai.projects import AIProjectClient
from azure.ai.evaluation import (
    AIAgentConverter, evaluate, ToolCallAccuracyEvaluator, IntentResolutionEvaluator, 
    TaskAdherenceEvaluator, CodeVulnerabilityEvaluator, ContentSafetyEvaluator, 
    IndirectAttackEvaluator)

from azure.identity import DefaultAzureCredential

def run_evaluation():
    """Demonstrate how to evaluate an AI agent using the Azure AI Project SDK"""
    current_dir = Path(__file__).parent
    eval_queries_path = current_dir / "eval-queries.json"
    eval_input_path = current_dir / f"eval-input.jsonl"
    eval_output_path = current_dir / f"eval-output.json"

    env_path = current_dir / "../src/.env"
    load_dotenv(dotenv_path=env_path)

    # Get AI project parameters from environment variables
    project_endpoint = os.environ.get("AZURE_EXISTING_AIPROJECT_ENDPOINT")
    parsed_endpoint = urlparse(project_endpoint)
    model_endpoint = f"{parsed_endpoint.scheme}://{parsed_endpoint.netloc}"
    deployment_name = os.getenv("AZURE_AI_AGENT_DEPLOYMENT_NAME")
    agent_name = os.environ.get("AZURE_AI_AGENT_NAME")
    agent_id = os.environ.get("AZURE_EXISTING_AGENT_ID")

    # Initialize the AIProjectClient and related entities
    credential = DefaultAzureCredential()
    ai_project = AIProjectClient(
        credential=credential,
        endpoint=project_endpoint,
        api_version = "2025-05-15-preview" # Evaluations yet not supported on stable (api_version="2025-05-01")
    )
    model_config = {
        "azure_deployment": deployment_name,
        "azure_endpoint": model_endpoint,
        "api_version": "",
    }
    thread_data_converter = AIAgentConverter(ai_project)

    # Look up the agent by name if agent Id is not provided
    if not agent_id and agent_name:
        for agent in ai_project.agents.list_agents():
            if agent.name == agent_name:
                agent_id = agent.id
                break
                
    if not agent_id:
        raise ValueError("Agent ID not found. Please provide a valid agent ID or name.") 
    
    agent = ai_project.agents.get_agent(agent_id)

    # Read data input file 
    with open(eval_queries_path, "r", encoding="utf-8") as f:
        test_data = json.load(f)
    
    # Execute the test data against the agent and prepare the evaluation input
    with open(eval_input_path, "w", encoding="utf-8") as f:        

        for row in test_data:
            # Create a new thread for each query to isolate conversations
            thread = ai_project.agents.threads.create()
            
            # Create the user query
            ai_project.agents.messages.create(
                thread.id, role=MessageRole.USER, content=row.get("query")
            )

            # Run agent on thread and measure performance
            start_time = time.time()
            run = ai_project.agents.runs.create_and_process(
                thread_id=thread.id, agent_id=agent.id
            )
            end_time = time.time()

            if run.status != RunStatus.COMPLETED:
                raise ValueError(run.last_error or "Run failed to complete")

            metrics = {
                "server-run-duration-in-seconds": (
                    run.completed_at - run.created_at
                ).total_seconds(),
                "client-run-duration-in-seconds": end_time - start_time,
                "completion-tokens": run.usage.completion_tokens,
                "prompt-tokens": run.usage.prompt_tokens,
                "ground-truth": row.get("ground-truth", '')
            }

            # Add thread data + operational metrics to the evaluation input
            evaluation_data = thread_data_converter.prepare_evaluation_data(thread_ids=thread.id)

            eval_item = evaluation_data[0]
            eval_item["metrics"] = metrics
            f.write(json.dumps(eval_item) + "\n")   
        

    # Now, run a sample set of evaluators using the evaluation input
    # See https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/agent-evaluate-sdk
    # for the full list of evaluators availalbe
    results = evaluate(
        evaluation_name="evaluation-test",
        data=eval_input_path,
        evaluators={
            "operational_metrics": OperationalMetricsEvaluator(),
            "tool_call_accuracy": ToolCallAccuracyEvaluator(model_config=model_config),
            "intent_resolution": IntentResolutionEvaluator(model_config=model_config),
            "task_adherence": TaskAdherenceEvaluator(model_config=model_config),
            "code_vulnerability": CodeVulnerabilityEvaluator(credential=credential, azure_ai_project=project_endpoint),  
            "content_safety": ContentSafetyEvaluator(credential=credential, azure_ai_project=project_endpoint),
            "indirect_attack": IndirectAttackEvaluator(credential=credential, azure_ai_project=project_endpoint)
        },
        output_path=eval_output_path, # raw evaluation results
        azure_ai_project=project_endpoint, # if you want results uploaded to AI Foundry
    )

    # Print the evaluation results
    print_eval_results(results, eval_input_path, eval_output_path)
    
    return results

class OperationalMetricsEvaluator:
    """Propagate operational metrics to the final evaluation results"""
    def __init__(self):
        pass
    def __call__(self, *, metrics: dict, **kwargs):
        return metrics


def print_eval_results(results, input_path, output_path):
    """Print the evaluation results in a formatted table"""    
    metrics = results.get("metrics", {})

    # Get the maximum length for formatting
    key_len = max(len(key) for key in metrics.keys()) + 5
    value_len = 20
    full_len = key_len + value_len + 5
    
    # Format the header
    print("\n" + "=" * full_len)
    print("Evaluation Results".center(full_len))
    print("=" * full_len)
    
    # Print all metrics, see evaluation output file for full details
    print(f"{'Metric':<{key_len}} | {'Value'}")
    print("-" * (key_len) + "-+-" + "-" * value_len)
    
    for key, value in sorted(metrics.items()):
        if isinstance(value, float):
            formatted_value = f"{value:.2f}"
        else:
            formatted_value = str(value)
        
        print(f"{key:<{key_len}} | {formatted_value}")
    
    print("=" * full_len + "\n")

    # Print additional information
    print(f"Evaluation input: {input_path}")
    print(f"Evaluation output: {output_path}")
    if results.get("studio_url") is not None:
        print(f"AI Foundry URL: {results['studio_url']}")

    print("\n" + "=" * full_len + "\n")


if __name__ == "__main__":
    try:
        run_evaluation()
    except Exception as e:
        print(f"Error during evaluation: {e}")

