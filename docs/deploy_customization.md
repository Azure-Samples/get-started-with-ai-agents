
# Getting Started with Agents Using Azure AI Foundry: Deployment customization

This document describes how to customize the deployment of the Agents Chat with Azure AI Foundry. Once you follow the steps here, you can run `azd up` as described in the [Deploying](./../README.md#deploying-steps) steps.

* [Use existing resources](#use-existing-resources)
* [Enabling and disabling resources provision](#enabling-and-disabling-resources-provision)
* [Customizing resource names](#customizing-resource-names)
* [Customizing model deployments](#customizing-model-deployments)

## Use existing resources
Be default, this template provisions a new resource group along with other resources.   If you already have provisioned Azure AI Foundry and Azure AI Foundry Project (not a hub based project), you might reuse these resources by setting:

To find the value:

1. open the azure portal
1. navigate to the AI foundry resource
1. select projects in the sidebar and open the desired project
1. go to 'Resource Management' -> 'Properties' in the sidebar
1. copy the value from 'Resource ID'

```shell
azd env set AZURE_EXISTING_AIPROJECT_RESOURCE_ID "subscriptions/<your-subscription-id>/resourceGroups/<resourcegroup>/providers/Microsoft.CognitiveServices/accounts/<ai-foundry-resource>/projects/<your-project-name>"
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

* `AZURE_AIPROJECT_NAME` - The name of the Azure AI Foundry project
* `AZURE_AISERVICES_NAME` - The name of the Azure AI Foundry
* `AZURE_STORAGE_ACCOUNT_NAME` - The name of the Storage Account
* `AZURE_APPLICATION_INSIGHTS_NAME` - The name of the Application Insights instance
* `AZURE_LOG_ANALYTICS_WORKSPACE_NAME` - The name of the Log Analytics workspace used by Application Insights

To override any of those resource names, run `azd env set <key> <value>` before running `azd up`.

## Customizing model deployments

For more information on the Azure OpenAI models and non-Microsoft models that can be used in your deployment, view the [list of models supported by Azure AI Agent Service](https://learn.microsoft.com/azure/ai-services/agents/concepts/model-region-support).

To customize the model deployments, you can set the following environment variables:

### Using a different chat model

Change the agent model format (either OpenAI or Microsoft):

```shell
azd env set AZURE_AI_AGENT_MODEL_FORMAT Microsoft
```

Change the agent model name:

```shell
azd env set AZURE_AI_AGENT_MODEL_NAME gpt-4o-mini
```

Set the version of the agent model:

```shell
azd env set AZURE_AI_AGENT_MODEL_VERSION 2024-07-18
```

### Setting capacity and deployment SKU

For quota regions, you may find yourself needing to modify the default capacity and deployment SKU using environment variables as below. The default tokens per minute deployed in this template is 80,000 for agent model and 50,000 for the embedding model that is enough for all operations.  If the region has quota less the these numbers, you will be prompt to input a lower capacity up to the available limit.

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