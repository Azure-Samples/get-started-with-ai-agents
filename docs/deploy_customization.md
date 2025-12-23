
# Getting Started with Agents Using Microsoft Foundry: Deployment customization

This document describes how to customize the deployment of the Agents Chat with Microsoft Foundry. Once you follow the steps here, you can run `azd up` as described in the section below.

* [Use existing resources](#use-existing-resources)
* [Enabling and disabling resources provision](#enabling-and-disabling-resources-provision)
* [Customizing resource names](#customizing-resource-names)
* [Customizing model deployments](#customizing-model-deployments)

## Use existing resources
Be default, this template provisions a new resource group along with other resources.   If you already have provisioned Microsoft Foundry and Microsoft Foundry Project (not a hub based project), you might reuse these resources by setting:

To find the value:

1. Open the azure portal
2. Navigate to the AI foundry resource
3. Select projects in the sidebar and open the desired project
4. Oo to 'Resource Management' -> 'Properties' in the sidebar
5. Copy the value from 'Resource ID'

```shell
azd env set AZURE_EXISTING_AIPROJECT_RESOURCE_ID "/subscriptions/<your-azure-subid>/resourceGroups/<your-rg>/providers/Microsoft.CognitiveServices/accounts/<your-ai-services-account-name>/projects/<your-project-name>"
```

Notices that Application Insight and AI Search will not be created in this scenario.


## Enabling and disabling resources provision

By default, provisioning Application Insights is enabled, and AI Search is disabled.  The default setting can be changed by:

* To enable AI Search, run `azd env set USE_AZURE_AI_SEARCH_SERVICE true`
* To disable Application Insights, run `azd env set USE_APPLICATION_INSIGHTS false`

Once you disable these resources, they will not be deployed when you run `azd up`.

## Customizing resource names

By default, this template will use a naming convention with unique strings to prevent naming collisions within Azure.
To override default naming conventions, the following keys can be set:

* `AZURE_AIPROJECT_NAME` - The name of the Microsoft Foundry project
* `AZURE_AISERVICES_NAME` - The name of the Microsoft Foundry
* `AZURE_STORAGE_ACCOUNT_NAME` - The name of the Storage Account
* `AZURE_APPLICATION_INSIGHTS_NAME` - The name of the Application Insights instance
* `AZURE_LOG_ANALYTICS_WORKSPACE_NAME` - The name of the Log Analytics workspace used by Application Insights

To override any of those resource names, run `azd env set <key> <value>` before running `azd up`.

## Customizing model deployments

For more information on the Azure OpenAI models and non-Microsoft models that can be used in your deployment, view the [list of models supported by Foundry Agent Service](https://learn.microsoft.com/azure/ai-services/agents/concepts/model-region-support).

To customize the model deployments, you can set the following environment variables:

### Using a different chat model

Change the agent model format (either OpenAI or Microsoft):

```shell
azd env set AZURE_AI_AGENT_MODEL_FORMAT Microsoft
```

Change the agent model name:

```shell
azd env set AZURE_AI_AGENT_MODEL_NAME gpt-5-mini
```

Set the version of the agent model:

```shell
azd env set AZURE_AI_AGENT_MODEL_VERSION 2025-08-07
```

### Setting models, capacity, and deployment SKU

By default, this template sets the agent model deployment capacity to 80,000 tokens per minute. For AI Search, the embedding model requires a capacity of 50,000 tokens per minute. Due to current Bicep limitations, only the chat model quota is validated when you select a location during `azd up`. If you want to change these defaults, set the desired region using `azd env set AZURE_LOCATION <region>` (for example, `eastus`) to bypass quota validation. Follow the instructions below to update the model settings before running `azd up`.

Change the default capacity (in thousands of tokens per minute) of the agent deployment:

```shell
azd env set AZURE_AI_AGENT_DEPLOYMENT_CAPACITY 50
```

Change the SKU of the agent deployment:

```shell
azd env set AZURE_AI_AGENT_DEPLOYMENT_SKU Standard
```

Change the default capacity (in thousands of tokens per minute) of the embeddings deployment:

```shell
azd env set AZURE_AI_EMBED_DEPLOYMENT_CAPACITY 50
```

Change the SKU of the embeddings deployment:

```shell
azd env set AZURE_AI_EMBED_DEPLOYMENT_SKU Standard
```

Set the embedding model dimensionality (only when using AI Search):

```shell
azd env set AZURE_AI_EMBED_DIMENSIONS 1536
```
