# Getting Started with Agents Using Azure AI Foundry

The agent leverages the Azure AI Agent service and utilizes file search for knowledge retrieval from uploaded files, enabling it to generate responses with citations. The solution also includes built-in monitoring capabilities with tracing to ensure easier troubleshooting and optimized performance.

<div style="text-align:center;">

[**SOLUTION OVERVIEW**](#solution-overview) \| [**GETTING STARTED**](#getting-started) \| [**LOCAL DEVELOPMENT**](#local-development) \| [**RESOURCE CLEAN-UP**](#resource-clean-up) \| [**GUIDANCE**](#guidance) \| [**TROUBLESHOOTING**](./docs/troubleshooting.md)

</div>

## Solution Overview

This solution deploys a web-based chat application with an AI agent running in Azure Container App.

The agent leverages the Azure AI Agent service and utilizes Azure AI Search for knowledge retrieval from uploaded files, enabling it to generate responses with citations. The solution also includes built-in monitoring capabilities with tracing to ensure easier troubleshooting and optimized performance.

This solution creates an Azure AI Foundry project and Azure AI services. More details about the resources can be found in the [resources](#resources) documentation. There are options to enable logging, tracing, and monitoring.

Instructions are provided for deployment through GitHub Codespaces, VS Code Dev Containers, and your local development environment.

### Solution Architecture

![Architecture diagram showing that user input is provided to the Azure Container App, which contains the app code. With user identity and resource access through managed identity, the input is used to form a response. The input and the Azure monitor are able to use the Azure resources deployed in the solution: Application Insights, Azure AI Foundry Project, Azure AI Services, Storage account, Azure Container App, and Log Analytics Workspace.](docs/images/architecture.png)

The app code runs in Azure Container App to process the user input and generate a response to the user. It leverages Azure AI projects and Azure AI services, including the model and agent.

### Key Features

- **[Knowledge Retrieval](./docs/deploy_customization.md#enabling-and-disabling-resources-provision)**<br/>
The AI agent uses file search or Azure AI Search to retrieve knowledge from uploaded files.

- **[Customizable AI Model Deployment](./docs/deploy_customization.md#customizing-model-deployments)**<br/>
The solution allows users to configure and deploy AI models, such as gpt-4o-mini, with options to adjust model capacity, and knowledge retrieval methods.

- **[Built-in Monitoring and Tracing](./docs/other_features.md#tracing-and-monitoring)**<br/>
Integrated monitoring capabilities, including Azure Monitor and Application Insights, enable tracing and logging for easier troubleshooting and performance optimization.

- **[Flexible Deployment Options](./docs/deployment.md)**<br/>
The solution supports deployment through GitHub Codespaces, VS Code Dev Containers, or local environments, providing flexibility for different development workflows.

- **[Agent Evaluation](./docs/other_features.md#agent-evaluation)**<br/>
This solution demonstrates how you can evaluate your agent's performance and quality during local development and incorporate it into monitoring and CI/CD workflow.

- **[AI Red Teaming Agent](./docs/other_features.md#ai-red-teaming-agent)**<br/>
Facilitates the creation of an AI Red Teaming Agent that can run batch automated scans for safety and security scans on your Agent solution to check your risk posture before deploying it into production.

<br/>

Here is a screenshot showing the chatting web application with requests and responses between the system and the user:

![Screenshot of chatting web application showing requests and responses between agent and the user.](docs/images/webapp_screenshot.png)

## Getting Started

| [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/Azure-Samples/get-started-with-ai-agents) | [![Open in Dev Containers](https://img.shields.io/static/v1?style=for-the-badge&label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/Azure-Samples/get-started-with-ai-agents) |
|---|---|

1. Click `Open in GitHub Codespaces` or `Dev Containers` button above
2. Wait for the environment to load
3. Run the following commands in the terminal:
   ```bash
   azd up
   ```
4. Follow the prompts to select your Azure subscription and region
5. Wait for deployment to complete (5-20 minutes) - you'll get a web app URL when finished

For detailed deployment options and troubleshooting, see the [full deployment guide](./docs/deployment.md).
**After deployment, try these [sample questions](./docs/sample_questions.md) to test your agent.**

## Local Development

For developers who want to run the application locally or customize the agent:

- **[Local Development Guide](./docs/local_development.md)** - Set up a local development environment, customize the frontend (starting with AgentPreview.tsx), modify agent instructions and tools, and use evaluation to improve your code.

This guide covers:
- Environment setup and prerequisites
- Running the development server locally
- Frontend customization and backend communication
- Agent instructions and tools modification
- File management and agent recreation
- Using agent evaluation for code improvement


## Resource Clean-up

To prevent incurring unnecessary charges, it's important to clean up your Azure resources after completing your work with the application.

- **When to Clean Up:**
  - After you have finished testing or demonstrating the application.
  - If the application is no longer needed or you have transitioned to a different project or environment.
  - When you have completed development and are ready to decommission the application.

- **Deleting Resources:**
  To delete all associated resources and shut down the application, execute the following command:
  
    ```bash
    azd down
    ```

    Please note that this process may take up to 20 minutes to complete.

⚠️ Alternatively, you can delete the resource group directly from the Azure Portal to clean up resources.

## Guidance

### Costs

Pricing varies per region and usage, so it isn't possible to predict exact costs for your usage.
The majority of the Azure resources used in this infrastructure are on usage-based pricing tiers.

You can try the [Azure pricing calculator](https://azure.microsoft.com/pricing/calculator) for the resources:

- **Azure AI Foundry**: Free tier. [Pricing](https://azure.microsoft.com/pricing/details/ai-studio/)  
- **Azure Storage Account**: Standard tier, LRS. Pricing is based on storage and operations. [Pricing](https://azure.microsoft.com/pricing/details/storage/blobs/)  
- **Azure AI Services**: S0 tier, defaults to gpt-4o-mini. Pricing is based on token count. [Pricing](https://azure.microsoft.com/pricing/details/cognitive-services/)  
- **Azure Container App**: Consumption tier with 0.5 CPU, 1GiB memory/storage. Pricing is based on resource allocation, and each month allows for a certain amount of free usage. [Pricing](https://azure.microsoft.com/pricing/details/container-apps/)  
- **Log analytics**: Pay-as-you-go tier. Costs based on data ingested. [Pricing](https://azure.microsoft.com/pricing/details/monitor/)  
- **Agent Evaluations**: Incurs the cost of your provided model deployment used for local evaluations.  
- **AI Red Teaming Agent**: Leverages Azure AI Risk and Safety Evaluations to assess attack success from the automated AI red teaming scan. Users are billed based on the consumption of Risk and Safety Evaluations as listed in [our Azure pricing page](https://azure.microsoft.com/pricing/details/ai-foundry/). Click on the tab labeled “Complete AI Toolchain” to view the pricing details.

⚠️ To avoid unnecessary costs, remember to take down your app if it's no longer in use,
either by deleting the resource group in the Portal or running `azd down`.

### Security guidelines

This template also uses [Managed Identity](https://learn.microsoft.com/entra/identity/managed-identities-azure-resources/overview) for local development and deployment.

To ensure continued best practices in your own repository, we recommend that anyone creating solutions based on our templates ensure that the [Github secret scanning](https://docs.github.com/code-security/secret-scanning/about-secret-scanning) setting is enabled.

You may want to consider additional security measures, such as:

- Enabling Microsoft Defender for Cloud to [secure your Azure resources](https://learn.microsoft.com/azure/defender-for-cloud/).
- Protecting the Azure Container Apps instance with a [firewall](https://learn.microsoft.com/azure/container-apps/waf-app-gateway) and/or [Virtual Network](https://learn.microsoft.com/azure/container-apps/networking?tabs=workload-profiles-env%2Cazure-cli).

> **Important Security Notice** <br/>
This template, the application code and configuration it contains, has been built to showcase Microsoft Azure specific services and tools. We strongly advise our customers not to make this code part of their production environments without implementing or enabling additional security features.  <br/><br/>
For a more comprehensive list of best practices and security recommendations for Intelligent Applications, [visit our official documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/).

### Resources

This template creates everything you need to get started with Azure AI Foundry:

| Resource | Description |
|----------|-------------|
| [Azure AI Project](https://learn.microsoft.com/azure/ai-studio/how-to/create-projects) | Provides a collaborative workspace for AI development with access to models, data, and compute resources |
| [Azure OpenAI Service](https://learn.microsoft.com/azure/ai-services/openai/) | Powers the AI agents for conversational AI and intelligent search capabilities. Default models deployed are gpt-4o-mini, but any Azure AI models can be specified per the [documentation](docs/deploy_customization.md#customizing-model-deployments) |
| [Azure Container Apps](https://learn.microsoft.com/azure/container-apps/) | Hosts and scales the web application with serverless containers |
| [Azure Container Registry](https://learn.microsoft.com/azure/container-registry/) | Stores and manages container images for secure deployment |
| [Storage Account](https://learn.microsoft.com/azure/storage/blobs/) | Provides blob storage for application data and file uploads |
| [AI Search Service](https://learn.microsoft.com/azure/search/) | *Optional* - Enables hybrid search capabilities combining semantic and vector search |
| [Application Insights](https://learn.microsoft.com/azure/azure-monitor/app/app-insights-overview) | *Optional* - Provides application performance monitoring, logging, and telemetry for debugging and optimization |
| [Log Analytics Workspace](https://learn.microsoft.com/azure/azure-monitor/logs/log-analytics-workspace-overview) | *Optional* - Collects and analyzes telemetry data for monitoring and troubleshooting |

## Troubleshooting

For solutions to common deployment, container app, and agent issues, see the [Troubleshooting Guide](./docs/troubleshooting.md).


## Disclaimers

To the extent that the Software includes components or code used in or derived from Microsoft products or services, including without limitation Microsoft Azure Services (collectively, “Microsoft Products and Services”), you must also comply with the Product Terms applicable to such Microsoft Products and Services. You acknowledge and agree that the license governing the Software does not grant you a license or other right to use Microsoft Products and Services. Nothing in the license or this ReadMe file will serve to supersede, amend, terminate or modify any terms in the Product Terms for any Microsoft Products and Services.

You must also comply with all domestic and international export laws and regulations that apply to the Software, which include restrictions on destinations, end users, and end use. For further information on export restrictions, visit <https://aka.ms/exporting>.

You acknowledge that the Software and Microsoft Products and Services (1) are not designed, intended or made available as a medical device(s), and (2) are not designed or intended to be a substitute for professional medical advice, diagnosis, treatment, or judgment and should not be used to replace or as a substitute for professional medical advice, diagnosis, treatment, or judgment. Customer is solely responsible for displaying and/or obtaining appropriate consents, warnings, disclaimers, and acknowledgements to end users of Customer’s implementation of the Online Services.

You acknowledge the Software is not subject to SOC 1 and SOC 2 compliance audits. No Microsoft technology, nor any of its component technologies, including the Software, is intended or made available as a substitute for the professional advice, opinion, or judgement of a certified financial services professional. Do not use the Software to replace, substitute, or provide professional financial advice or judgment.  

BY ACCESSING OR USING THE SOFTWARE, YOU ACKNOWLEDGE THAT THE SOFTWARE IS NOT DESIGNED OR INTENDED TO SUPPORT ANY USE IN WHICH A SERVICE INTERRUPTION, DEFECT, ERROR, OR OTHER FAILURE OF THE SOFTWARE COULD RESULT IN THE DEATH OR SERIOUS BODILY INJURY OF ANY PERSON OR IN PHYSICAL OR ENVIRONMENTAL DAMAGE (COLLECTIVELY, “HIGH-RISK USE”), AND THAT YOU WILL ENSURE THAT, IN THE EVENT OF ANY INTERRUPTION, DEFECT, ERROR, OR OTHER FAILURE OF THE SOFTWARE, THE SAFETY OF PEOPLE, PROPERTY, AND THE ENVIRONMENT ARE NOT REDUCED BELOW A LEVEL THAT IS REASONABLY, APPROPRIATE, AND LEGAL, WHETHER IN GENERAL OR IN A SPECIFIC INDUSTRY. BY ACCESSING THE SOFTWARE, YOU FURTHER ACKNOWLEDGE THAT YOUR HIGH-RISK USE OF THE SOFTWARE IS AT YOUR OWN RISK.
