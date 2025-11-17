# Observability features

## Tracing and monitoring

**First, if tracing isn't enabled yet, enable tracing by setting the environment variable:**

```shell
azd env set ENABLE_AZURE_MONITOR_TRACING true
azd deploy
```

### Console traces

You can view console traces in the Azure portal. You can get the link to the resource group with the azd tool:

```shell
azd show
```

Or if you want to navigate from the Azure portal main page, select your resource group from the 'Recent' list, or by clicking the 'Resource groups' and searching your resource group there.

After accessing your resource group in Azure portal, choose your container app from the list of resources. Then open 'Monitoring' and 'Log Stream'. Choose the 'Application' radio button to view application logs. You can choose between real-time and historical using the corresponding radio buttons. Note that it may take some time for the historical view to be updated with the latest logs.

### Agent traces

You can view both the server-side and client-side traces, cost and evaluation data in Azure AI Foundry. Go to the agent under your project on the Azure AI Foundry page and then click 'Tracing'.

![Tracing Tab](./images/tracing_tab.png)

### Monitor

Once App Insights is connected to your foundry project, you can also visit the monitoring dashboard to view trends such as agent runs and tokens count, error rates, evaluation results, and other key metrics that help you monitor agent performance and usage.

![Monitor Dashboard](./images/agent_monitor.png)

## Continuous Evaluation

Continuous evaluation is an automated monitoring capability that continuously assesses your agent's quality, performance, and safety as it handles real user interactions in production.

During container startup, continuous evaluation is `enabled` by default and pre-configured with a sample evaluator set to evaluate up to `5` agent responses per hour. Continuous evaluation does not generate test inputs—instead, it evaluates real user conversations as they occur. This means evaluation runs are triggered only when actual users interact with your agent, and if there are no user interactions, there will be no evaluation entries.

To customize continuous evaluation from the Azure AI Foundry:

1. Go to [Azure AI Foundry Portal](https://ai.azure.com/) and sign in
2. Click on your project from the homepage
3. In the top navigation, select **Build**
4. In the left-hand menu, select **Agents**
5. Select **Monitor**
6. Choose the agent you want to enable continuous evaluation for from the agent list
7. Click on **Settings**
8. Select evaluators and adjust maximal number of runs per hour

![Configure Continuous Evaluation](./images/enable_cont_eval.png)

## Agent Evaluation

Azure AI Foundry offers a number of [built-in evaluators](https://learn.microsoft.com/azure/ai-foundry/how-to/develop/agent-evaluate-sdk) to measure the quality, efficiency, risk and safety of your agents. For example, intent resolution, tool call accuracy, and task adherence evaluators are targeted to assess the performance of agent workflow, while content safety evaluator checks for inappropriate content in the responses such as violence or hate. 
You can also create custom evaluators tailored to your specific requirements, including custom prompt-based evaluators or code-based evaluators that implement your unique assessment criteria.

In this template, we show how the evaluation of your agent can be intergrated into the test suite of your AI application.

You can use the [evaluation test script](../tests/test_evaluation.py) to validate your agent's performance using built-in Azure AI evaluators. The test demonstrates how to:
  - Define testing criteria using Azure AI evaluators (e.g., violence)
  - Run evaluation against specific test queries
  - Retrieve and analyze evaluation results

  The test reads the following environment variables:
  - `AZURE_EXISTING_AIPROJECT_ENDPOINT`: AI Project endpoint
  - `AZURE_EXISTING_AGENT_ID`: AI Agent Id in the format `agent_name:agent_version` (with fallback logic to look up the latest version by name using `AZURE_AI_AGENT_NAME`)
  - `AZURE_AI_AGENT_DEPLOYMENT_NAME`: The judge model deployment name used by evaluators

  **Note:** Most of these environment variables are generated locally in `.env` after executing `azd up`. To find the Agent ID remotely in the Azure AI Foundry Portal:

  1. Go to [Azure AI Foundry Portal](https://ai.azure.com/) and sign in
  2. Click on your project from the homepage
  3. In the top navigation, select **Build**
  4. In the left-hand menu, select **Agents**
  5. Locate your agent in the list - the agent name and version will be displayed
  6. The Agent ID follows the format: `{agent_name}:{agent_version}` (e.g., `agent-template-assistant:1`)
  
  ![Agent ID in Foundry UI](./images/agent_id_in_foundry_ui.png)

  To install required packages and run the evaluation test:  

  ```shell
  python -m pip install -r src/requirements.txt

  pytest tests/test_evaluation.py
  ```

  **Tip:** Add the `-s` flag to see detailed print output during test execution:
  ```shell
  pytest tests/test_evaluation.py -s
  ```

## AI Red Teaming Agent

The [AI Red Teaming Agent](https://learn.microsoft.com/azure/ai-foundry/concepts/ai-red-teaming-agent) is a powerful tool designed to help organizations proactively find security and safety risks associated with generative AI systems during design and development of generative AI models and applications.

In the [red teaming test script](../tests/test_red_teaming.py), you will be able to set up an AI Red Teaming Agent to run an automated scan of your agent in this sample. The test demonstrates how to:
- Create a red-teaming evaluation
- Generate taxonomies for risk categories (e.g., prohibited actions)
- Configure attack strategies (Flip, Base64) with multi-turn conversations
- Retrieve and analyze red teaming results

No test dataset or adversarial LLM is needed as the AI Red Teaming Agent will generate all the attack prompts for you.

To install required packages and run the red teaming test in your local development environment:  

```shell
python -m pip install -r src/requirements.txt

pytest tests/test_red_teaming.py
```

**Tip:** Add the `-s` flag to see detailed print output during test execution:
```shell
pytest tests/test_red_teaming.py -s
```

The test will generate output files in the `tests/data_folder` directory:
- `taxonomy_{agent_name}.json`: The generated taxonomy for red teaming
- `redteam_eval_output_items_{agent_name}.json`: Detailed results from the red teaming evaluation

Read more on supported attack techniques and risk categories in our [documentation](https://learn.microsoft.com/azure/ai-foundry/how-to/develop/run-scans-ai-red-teaming-agent).