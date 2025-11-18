# Observability features

Observability is a key aspect of building and maintaining high-quality AI applications. It encompasses monitoring, tracing, and evaluating the performance and behavior of AI systems to ensure they meet desired standards and provide a safe and reliable user experience. 

In **pre-deployment** stage, you can leverage [Agent Evaluation](#agent-evaluation) and [AI Red Teaming Agent](#ai-red-teaming-agent) features to assess and improve the quality, safety, and reliability of your AI agents before they are released to end users. You will establish a test baseline for your agent and continuously monitor its performance during development iterations. For example, you find 85% passing rate for [task completion rate](https://learn.microsoft.com/azure/ai-foundry/concepts/evaluation-evaluators/agent-evaluators#system-evaluation) to be the acceptance threshold for your agents before deployment.

In **post-deployment** stage, you can utilize [Tracing and monitoring](#tracing-and-monitoring) and [Continuous Evaluation](#continuous-evaluation) capabilities to maintain ongoing visibility into your agent's performance and behavior in production. With the baselines established in pre-deployment, you can set up alerts for a desirable passing rate, so that you can review the failing traces that helps you quickly identify and address any issues that may arise, ensuring a consistent and high-quality user experience.

## Prequisites 

Execute `azd up` to generate most of these environment variables in `.azure/.env`. To specify the Agent ID, navigate to the Azure AI Foundry Portal:

  1. Go to [Azure AI Foundry Portal](https://ai.azure.com/) and sign in
  2. Click on your project from the homepage
  3. In the top navigation, select **Build**
  4. In the left-hand menu, select **Agents**
  5. Locate your agent in the list - the agent name and version will be displayed
  6. The Agent ID follows the format: `{agent_name}:{agent_version}` (e.g., `agent-template-assistant:1`)

  ![Agent ID in Foundry UI](./images/agent_id_in_foundry_ui.png)

## Agent Evaluation

Azure AI Foundry offers a number of [built-in evaluators](https://learn.microsoft.com/azure/ai-foundry/concepts/observability#what-are-evaluators) to measure the quality, efficiency, risk and safety of your agents. For example, intent resolution, tool call accuracy, and task adherence evaluators are targeted to assess the end-to-end and tool call process quality of agent workflow, while content safety evaluator checks for inappropriate content in the responses such as violence or hate. 
You can also create custom evaluators tailored to your specific requirements, including custom prompt-based evaluators or code-based evaluators that implement your unique assessment criteria.

In this template, we show how the evaluation of your agent can be intergrated into the test suite of your AI application.

You can use the [evaluation test script](../tests/test_evaluation.py) to validate your agent's performance using built-in Azure AI evaluators. The test demonstrates how to:
  - Define testing criteria using Azure AI evaluators:
    - [Agent evaluators](https://learn.microsoft.com/azure/ai-foundry/concepts/evaluation-evaluators/agent-evaluators): process and system level evaluators specifically designed for agent workflows.
    - [Retrieval-augmented Generation (RAG) evaluators](https://learn.microsoft.com/azure/ai-foundry/concepts/evaluation-evaluators/rag-evaluators): evaluate the quality of end-to-end and retrieval process of RAG in agents or standalone systems.
    - [Risk and safety evaluators](https://learn.microsoft.com/azure/ai-foundry/concepts/evaluation-evaluators/risk-safety-evaluators): assess potential risks and safety concerns in agent responses.
    - [General purpose evaluators](https://learn.microsoft.com/azure/ai-foundry/concepts/evaluation-evaluators/general-purpose-evaluators): evaluate coherence and fluency in business writing scenarios.
    - [Textual similarity evaluators](https://learn.microsoft.com/azure/ai-foundry/concepts//evaluation-evaluators/textual-similarity-evaluators): measure semantic similarity of AI-generated texts with respect to expected ground truth texts.
  - Run evaluation against specific test queries
  - Retrieve and analyze evaluation results

  The test reads the following environment variables:
  - `AZURE_EXISTING_AIPROJECT_ENDPOINT`: AI Project endpoint
  - `AZURE_EXISTING_AGENT_ID`: AI Agent Id in the format `agent_name:agent_version` (with fallback logic to look up the latest version by name using `AZURE_AI_AGENT_NAME`)
  - `AZURE_AI_AGENT_DEPLOYMENT_NAME`: The judge model deployment name used by evaluators

  Follow the [prerequisites](#prerequisites) to set up these environment variables. To install required packages and run the evaluation test in your python environment:  

  ```shell
  python -m pip install -r src/requirements.txt

  pytest tests/test_evaluation.py
  ```

  **Tip:** Add the `-s` flag to see detailed print output during test execution:
  ```shell
  pytest tests/test_evaluation.py -s
  ```

  Upon completion, the test will display a **Report URL** in the output where you can review the detailed evaluation results in the Azure AI Foundry UI, including individual evaluator passing scores and explanations.

  ![Evaluation Report Link](./images/eval_link.png)

  ![Evaluation Report](./images/eval_report.png)

## AI Red Teaming Agent

The [AI Red Teaming Agent](https://learn.microsoft.com/azure/ai-foundry/concepts/ai-red-teaming-agent) is a powerful tool designed to help organizations proactively find security and safety risks associated with generative AI systems during design and development of generative AI models and applications.

In the [red teaming test script](../tests/test_red_teaming.py), you will be able to set up an AI Red Teaming Agent to run an automated scan of your agent in this sample. The test demonstrates how to:
- Create a red-teaming evaluation
- Generate taxonomies for risk categories (e.g., prohibited actions)
- Configure attack strategies (Flip, Base64) with multi-turn conversations
- Retrieve and analyze red teaming results

No test dataset or adversarial LLM is needed as the AI Red Teaming Agent will generate all the attack prompts for you.

  Follow the [prerequisites](#prerequisites) to set up these environment variables. To install required packages and run the red teaming test in your local development environment:  

```shell
python -m pip install -r src/requirements.txt

pytest tests/test_red_teaming.py
```

**Tip:** Add the `-s` flag to see detailed print output during test execution:
```shell
pytest tests/test_red_teaming.py -s
```

Upon completion, the test will display a **Report URL** in the output where you can review the detailed red teaming evaluation results in the Azure AI Foundry UI, including attack inputs, outcomes, and reasons.

![Red Teaming Report Link](./images/red_teaming_report_link.png)

![Red Teaming Evaluation Report](./images/red_teaming_report.png)

Read more on supported attack techniques and risk categories in our [documentation](https://learn.microsoft.com/azure/ai-foundry/how-to/develop/run-scans-ai-red-teaming-agent).

## Tracing and monitoring

**Enable tracing by setting the environment variable (if not already enabled):**

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
