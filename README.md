# Getting Started with Agents Using Azure AI Foundry 

MENU: [**FEATURES**](#features) \| [**GETTING STARTED**](#getting-started) \| [**CONFIGURE YOUR ENVIRONMENT**](#configure-your-environment)  \| [**DEPLOYMENT**](#deployment)  \| [**RESOURCE CLEAN-UP**](#resource-clean-up)  \| [**TRACING AND MONITORING**](#tracing-and-monitoring)  \| [**GUIDANCE**](#guidance) \| [**TROUBLESHOOTING**](#troubleshooting) 

## Important Security Notice

This template, the application code and configuration it contains, has been built to showcase Microsoft Azure specific services and tools. We strongly advise our customers not to make this code part of their production environments without implementing or enabling additional security features.  

For a more comprehensive list of best practices and security recommendations for Intelligent Applications, [visit our official documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/).

## Features

This solution deploys a web-based chat application with an AI agent running in Azure Container Apps. The agent leverages the Azure AI Agent service and utilizes Azure AI Search for knowledge retrieval from uploaded files, enabling it to generate responses with citations. The solution also includes built-in monitoring capabilities with tracing to ensure easier troubleshooting and optimized performance.

This solution creates an Azure AI Foundry hub, project and connected resources including Azure AI Services, AI Search and more. More details about the resources can be found in the [resources](#resources) documentation. There are options to enable Retrieval-Augmented Generation (RAG) and use logging, tracing, and monitoring. 

Instructions are provided for deployment through GitHub Codespaces, VS Code Dev Containers, and your local development environment.

#### Architecture diagram

![Architecture diagram showing that user input is provided to the Azure Container App, which contains the app code. With user identity and resource access through managed identity, the input is used to form a response. The input and the Azure monitor are able to use the Azure resources deployed in the solution: Application Insights, Azure AI Project, Azure AI Services, Azure AI Hub, Storage account, Azure Container App, Container Registry, Key Vault, and Log Analytics Workspace.](docs/architecture.png)
The app code runs in Azure Container apps to process the user input and generate a response to the user. It leverages Azure AI projects and Azure AI services, including the model and agent.

## Getting Started

### Quick Deploy

| [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/Azure-Samples/get-started-with-ai-agents) | [![Open in Dev Containers](https://img.shields.io/static/v1?style=for-the-badge&label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/Azure-Samples/get-started-with-ai-agents) | [![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2FAzure-Samples%2Fget-started-with-ai-agents%2Frefs%2Fheads%2Fmain%2Finfra%2Fmain.json) |
|---|---|---|

Github Codespaces and Dev Containers both allow you to download and deploy the code for development. You can also continue with local development. Once you have selected your environment, follow the instructions below to customize and deploy your solution.    

### Prerequisites 

#### Azure Account
If you do not have an Azure Subscription, you can sign up for a [free Azure account](https://azure.microsoft.com/free/) and create an Azure Subscription.

To deploy this Azure environment successfully, your Azure account (the account you authenticate with) must have the following permissions and prerequisites on the targeted Azure Subscription:

- **Microsoft.Authorization/roleAssignments/write** permissions at the subscription scope.  
  _(typically included if you have [Role Based Access Control Administrator](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles#role-based-access-control-administrator-preview), [User Access Administrator](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles#user-access-administrator), or [Owner](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles#owner) role)_
- **Microsoft.Resources/deployments/write** permissions at the subscription scope.

You can view the permissions for your account and subscription by going to Azure portal, clicking 'Subscriptions' under 'Navigation' and then choosing your subscription from the list. If you try to search for your subscription and it does not come up, make sure no filters are selected. After selecting your subscription, select 'Access control (IAM)' and you can see the roles that are assigned to your account for this subscription. If you want to see more information about the roles, you can go to the 'Role assignments' tab and search by your account name and then click the role you want to view more information about.

#### Required tools
Make sure the following tools are installed:

1. [Azure Developer CLI (azd)](https://aka.ms/install-azd) Install or update to the latest version. Instructions can be found on the linked page.
2. [Python 3.9+](https://www.python.org/downloads/)
3. [Git](https://git-scm.com/downloads)
4. [Docker Desktop](https://www.docker.com/products/docker-desktop/)

## Configure your Environment

This section details the customizable options for this solution, including agent model, knowledge retrieval, logging, tracing, and quota recommendations. If you want to proceed with the default settings, continue to the [deployment section](#deployment). 

#### Code
If you are using one of the [Quick Deploy options](#quick-deploy), open the codespace now. 

If you are not using any of the Quick Deploy options, download the project code:

```shell
git clone https://github.com/Azure-Samples/get-started-with-ai-agents.git
```
At this point you could make changes to the code if required. However, no changes are needed to deploy and test the app as shown in the next step.


#### Configurable Deployment Settings
When you start a deployment, most parameters will have default values. You can change the following default settings: 

| **Setting** | **Description** |  **Default value** |
|------------|----------------|  ------------|
| **Azure Region** | Select a region with quota which supports your selected model. |   |
| **Model** | Choose from the [list of models supported by Azure AI Agent Service](https://learn.microsoft.com/azure/ai-services/agents/concepts/model-region-support) for your selected region. | gpt-4o-mini |  
| **Model Format** | Choose from OpenAI or Microsoft, depending on your model. | OpenAI |  
| **Model Deployment Capacity** | Configure capacity for your model. Recommended value is 100k. | 30k |
| **Embedding Model** | Choose from text-embedding-3-large, text-embedding-3-small, and text-embedding-ada-002. This may only be deployed if Azure AI Search is enabled. |  text-embedding-3-small |
| **Embedding Model Capacity** | Configure capacity for your embedding model. |  30k |
| **Knowledge Retrieval** | Choose from OpenAI's file search or including Azure AI Search Index. |  OpenAI's file search |

For a detailed description of customizable fields and instructions, view the [deployment customization guide](docs/deploy_customization.md).

#### How to configure Agent model and version

By default, the template uses model `gpt-4o-mini`, version `2024-07-18` for text generation and `text-embedding-3-small` version `1` for embeddings. If you want to personalize your agent, you can change the default configuration for your agent. Additional details on changing your agent can be found in [customizing model deployments](docs/deploy_customization.md#customizing-model-deployments). For more information on the Azure OpenAI models and non-Microsoft models that can be used in your deployment, view the [list of models supported by Azure AI Agent Service](https://learn.microsoft.com/azure/ai-services/agents/concepts/model-region-support).

To specify the model (e.g. gpt-4o-mini, gpt-4o) that is deployed for the agent when `azd up` is called, set the following environment variables:
```shell
azd env set AZURE_AI_AGENT_MODEL_NAME <MODEL_NAME>
azd env set AZURE_AI_AGENT_MODEL_VERSION <MODEL_VERSION>
```

#### How to configure Agent knowledge retrieval
By default, the template deploys OpenAI's [file search](https://learn.microsoft.com/azure/ai-services/agents/how-to/tools/file-search?tabs=python&pivots=overview) for agent's knowledge retrieval. An agent also can perform search using the search index, deployed in Azure AI Search resource. The semantic index search represents so-called hybrid search i.e. it uses LLM to search for the relevant context in the provided index as well as embedding similarity search. This index is built from the `embeddings.csv` file, containing the embeddings vectors, followed by the contexts.
To use index search, please set the local environment variable `USE_AZURE_AI_SEARCH_SERVICE` to `true` during the `azd up` command. In this case the Azure AI Search resource will be deployed and used.

#### Logging
To enable logging to a file, navigate to `src/Dockerfile` and edit the code to uncomment the following line:

 ```
 # ENV APP_LOG_FILE=app.log
 ```

 By default the file name app.log is used. You can provide your own file name by replacing app.log with the desired log file name.

 **NOTE!** Any changes to the Dockerfile require a re-deployment in order for the changes to take effect.

The provided file logging implementation is intended for development purposes only, specifically for testing with a single client/worker. It should not be used in production environments after the R&D phase.

#### Tracing to Azure Monitor
To enable tracing to Azure Monitor, navigate to `src/Dockerfile` and modify the value of `ENABLE_AZURE_MONITOR_TRACING` environment variable to true:
```
ENV ENABLE_AZURE_MONITOR_TRACING=true
```
Note that the optional App Insights resource is required for tracing to Azure Monitor (it is created by default).

To enable message contents to be included in the traces, set the following environment variable to true in the same `Dockerfile`. Note that the messages may contain personally identifiable information.

```code
ENV AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=true
```

#### Quota Recommendations

The default for the model capacity in deployment is 30k tokens. For optimal performance, it is recommended to increase to 100k tokens. You can change the capacity by following the steps in [setting capacity and deployment SKU](docs/deploy_customization.md#customizing-model-deployments).

* Navigate to the home screen of the [Azure AI Foundry Portal](https://ai.azure.com/)
* Select Quota Management buttom at the bottom of the home screen
* In the Quota tab, click the GlobalStandard dropdown and select the model and region you are using for this accelerator to see your available quota. Please note gpt-4o-mini and text-embedding-ada-002 are used as default.
* Request more quota or delete any unused model deployments as needed.

## Deployment

### Deployment Options

Pick from the options below to see step-by-step instructions for: GitHub Codespaces, VS Code Dev Containers, and Local Environments. If you encounter an issue with any of the following options, try a different one. 

<details>
  <summary><b>GitHub Codespaces</b></summary>

#### GitHub Codespaces

You can run this template virtually by using GitHub Codespaces. The button will open a web-based VS Code instance in your browser:

1. Open the template (this may take several minutes):

    [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/Azure-Samples/get-started-with-ai-agents)

2. Open a terminal window
3. Continue with the [deploying steps](#deploying-steps)

</details>

<details>
  <summary><b>VS Code Dev Containers</b></summary>

#### VS Code Dev Containers

A related option is VS Code Dev Containers, which will open the project in your local VS Code using the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers):

1. Start Docker Desktop (install it if not already installed [Docker Desktop](https://www.docker.com/products/docker-desktop/))
2. Open the project:

    [![Open in Dev Containers](https://img.shields.io/static/v1?style=for-the-badge&label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/Azure-Samples/get-started-with-ai-agents)

3. In the VS Code window that opens, once the project files show up (this may take several minutes), open a terminal window.
4. Continue with the [deploying steps](#deploying-steps)
</details>

<details>
  <summary><b>Local Environment</b></summary>

#### Local Environment

1. Confirm that you have the required tools installed from the [prerequisites](#prerequisites) section and the code downloaded from the [code](#code) section
2.  Open the project folder in your terminal or editor
3. Continue with the [deploying steps](#deploying-steps)
</details>

<details>
  <summary><b>Local Development Server</b></summary>

#### Local Development Server

You can optionally use a local development server to test app changes locally. Make sure you first [deployed the app](#deploying-steps) to Azure before running the development server.

1. Create a [Python virtual environment](https://docs.python.org/3/tutorial/venv.html#creating-virtual-environments) and activate it.

    On Windows:

    ```shell
    python -m venv .venv
    .venv\scripts\activate
    ```

    On Linux:

    ```shell
    python3 -m venv .venv
    source .venv/bin/activate
    ```

2. Navigate to the `src` directory:

    ```shell
    cd src
    ```

3. Install required Python packages:

    ```shell
    python -m pip install -r requirements.txt
    ```

4. Duplicate `src/.env.sample` and name to `.env`.

5. Fill in the environment variables in `.env`.

6. Run the local server:

    ```shell
    python -m uvicorn "api.main:create_app" --factory --reload
    ```

7. Click 'http://127.0.0.1:8000' in the terminal, which should open a new tab in the browser.

8. Enter your message in the box.
</details>

### Deploying Steps

Once you've opened the project in [Codespaces](#github-codespaces) or in [Dev Containers](#vs-code-dev-containers) or [locally](#local-environment), you can deploy it to Azure following the following steps. 

1. Login to Azure:

    ```shell
    azd auth login
    ```

2. (Optional) If you would like to customize the deployment to [disable resources](docs/deploy_customization.md#disabling-resources), [customize resource names](docs/deploy_customization.md#customizing-resource-names), [customize the models](docs/deploy_customization.md#customizing-model-deployments) or [increase quota](docs/deploy_customization.md#setting-capacity-and-deployment-sku), you can follow those steps now. 

    ⚠️ **NOTE!** For optimal performance, the recommended quota is 100k tokens per minute. If you have the capacity, we recommend increasing the quota by running the following command: 
    ```shell
    azd env set AZURE_AI_AGENT_DEPLOYMENT_CAPACITY 100
    ```
    ⚠️ If you do not increase your quota, you may encounter rate limit issues. If needed, you can increase the quota after deployment by editing your model in the Models and Endpoints tab of the [Azure AI Foundry Portal](https://ai.azure.com/).

3. Provision and deploy all the resources by running the following in get-started-with-ai-agents directory:

    ```shell
    azd up
    ```

4. You will be prompted to provide an `azd` environment name (like "azureaiapp"), select a subscription from your Azure account, and select a location which has quota for all the resources. Then, it will provision the resources in your account and deploy the latest code. 

    * For guidance on selecting a region with quota and model availability, follow the instructions in the [quota recommendations](#quota-recommendations-optional) section and ensure that your model is available in your selected region by checking the [list of models supported by Azure AI Agent Service](https://learn.microsoft.com/azure/ai-services/agents/concepts/model-region-support)
    * This deployment will take 7-10 minutes to provision the resources in your account and set up the solution with sample data.
    * If you get an error or timeout with deployment, changing the location can help, as there may be availability constraints for the resources. You can do this by running `azd down` and deleting the `.azure` folder from your code, and then running `azd up` again and selecting a new region.

    **NOTE!** If you get authorization failed and/or permission related errors during the deployment, please refer to the Azure account requirements in the [Prerequisites](#prerequisites) section. If you were recently granted these permissions, it may take a few minutes for the authorization to apply.

5. When `azd` has finished deploying, you'll see an endpoint URI in the command output. Visit that URI, and you should see the app! 🎉

    * From here, you can interact with the agent. Try chatting with the agent by asking for a joke, or you could try a more specific query to see the agent's citation capabilities. By default, this solution uploads two documents from the `src/files` folder. To see the agent use this information, try asking about Contoso's products.

    * You can view information about your deployment with:
        ```shell
        azd show
        ```

6. (Optional) Now that your app has deployed, you can view your resources in the Azure Portal and your deployments in Azure AI Foundry. 
    * In the [Azure Portal](https://portal.azure.com/), navigate to your environment's resource group. The name will be `rg-[your environment name]`. Here, you should see your container app, storage account, and all of the other [resources](#resources) that are created in the deployment.
    * In the [Azure AI Foundry Portal](https://ai.azure.com/), select your project. If you navigate to the Assistants tab, you should be able to view your new assistant, named `agent-template-assistant`. If you navigate to the Models and Endpoints tab, you should see your AI Services connection with your model deployments. 

7. (Optional) If you make further modification to the app code, you can deploy the updated version with:

    ```shell
    azd deploy
    ```
    You can get more detailed output with the ```--debug``` parameter.
    ```shell
    azd deploy --debug
    ```
    >**Important:**
    >
    >Check carefully for any errors during deployment and the startup phase of the Azure Container App. If the container fails to start correctly after deployment, the application changes you made will not take effect, and Azure Container Apps will continue serving requests from the previous stable revision.

8. (Optional) You can use a local development server to test app changes locally. To do so, follow the steps in [local deployment server](#local-development-server) after your app is deployed.

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

## Tracing and Monitoring

You can view console logs in Azure portal. You can get the link to the resource group with the azd tool:
```shell
azd show
```

Or if you want to navigate from the Azure portal main page, select your resource group from the 'Recent' list, or by clicking the 'Resource groups' and searching your resource group there.

After accessing you resource group in Azure portal, choose your container app from the list of resources. Then open 'Monitoring' and 'Log Stream'. Choose the 'Application' radio button to view application logs. You can choose between real-time and historical using the corresponding radio buttons. Note that it may take some time for the historical view to be updated with the latest logs.

If you enabled logging to a file, you can view the log file by choosing 'Console' under the 'Monitoring' (same location as above for the console traces), opening the default console and then for example running the following command (replace app.log with the actual name of your log file):

```shell
more app.log
```

You can view the App Insights tracing in Azure AI Foundry. Select your project on the Azure AI Foundry page and then click 'Tracing'.

## Guidance

#### Costs

Pricing varies per region and usage, so it isn't possible to predict exact costs for your usage.
The majority of the Azure resources used in this infrastructure are on usage-based pricing tiers.
However, Azure Container Registry has a fixed cost per registry per day.

You can try the [Azure pricing calculator](https://azure.microsoft.com/en-us/pricing/calculator) for the resources:

* Azure AI Foundry: Free tier. [Pricing](https://azure.microsoft.com/pricing/details/ai-studio/)
* Azure AI Search: Standard tier, S1. Pricing is based on the number of documents and operations. [Pricing](https://azure.microsoft.com/pricing/details/search/)
* Azure Storage Account: Standard tier, LRS. Pricing is based on storage and operations. [Pricing](https://azure.microsoft.com/pricing/details/storage/blobs/)
* Azure Key Vault: Standard tier. Pricing is based on the number of operations. [Pricing](https://azure.microsoft.com/pricing/details/key-vault/)
* Azure AI Services: S0 tier, defaults to gpt-4o-mini and text-embedding-ada-002 models. Pricing is based on token count. [Pricing](https://azure.microsoft.com/pricing/details/cognitive-services/)
* Azure Container App: Consumption tier with 0.5 CPU, 1GiB memory/storage. Pricing is based on resource allocation, and each month allows for a certain amount of free usage. [Pricing](https://azure.microsoft.com/pricing/details/container-apps/)
* Azure Container Registry: Basic tier. [Pricing](https://azure.microsoft.com/pricing/details/container-registry/)
* Log analytics: Pay-as-you-go tier. Costs based on data ingested. [Pricing](https://azure.microsoft.com/pricing/details/monitor/)

⚠️ To avoid unnecessary costs, remember to take down your app if it's no longer in use,
either by deleting the resource group in the Portal or running `azd down`.

#### Security guidelines

This template uses Azure AI Foundry connections to communicate between resources, which stores keys in Azure Key Vault.
This template also uses [Managed Identity](https://learn.microsoft.com/entra/identity/managed-identities-azure-resources/overview) for local development and deployment.

To ensure continued best practices in your own repository, we recommend that anyone creating solutions based on our templates ensure that the [Github secret scanning](https://docs.github.com/code-security/secret-scanning/about-secret-scanning) setting is enabled.

You may want to consider additional security measures, such as:

* Enabling Microsoft Defender for Cloud to [secure your Azure resources](https://learn.microsoft.com/azure/defender-for-cloud/).
* Protecting the Azure Container Apps instance with a [firewall](https://learn.microsoft.com/azure/container-apps/waf-app-gateway) and/or [Virtual Network](https://learn.microsoft.com/azure/container-apps/networking?tabs=workload-profiles-env%2Cazure-cli).

#### Resources

This template creates everything you need to get started with Azure AI Foundry:

* [AI Hub Resource](https://learn.microsoft.com/azure/ai-studio/concepts/ai-resources)
* [AI Project](https://learn.microsoft.com/azure/ai-studio/how-to/create-projects)
* [Azure AI Service](https://learn.microsoft.com/azure/ai-services): Default models deployed are gpt-4o-mini and text-embedding-ada-002, but any Azure AI models can be specified per the [documentation](docs/deploy_customization.md#customizing-model-deployments).
* [AI Search Service](https://learn.microsoft.com/azure/search/) *(Optional, enabled by default)*

The template also includes dependent resources required by all AI Hub resources:

* [Storage Account](https://learn.microsoft.com/azure/storage/blobs/)
* [Key Vault](https://learn.microsoft.com/azure/key-vault/general/)
* [Application Insights](https://learn.microsoft.com/azure/azure-monitor/app/app-insights-overview) *(Optional, enabled by default)*
* [Container Registry](https://learn.microsoft.com/azure/container-registry/) *(Optional, enabled by default)*

## Troubleshooting

#### Provisioning and Deployment Failures
* If you have an issue is with timeouts or provisioning resources, changing the location of your resource group can help, as there may be availability constrains for resources. Call `azd down` and remove your current resources, and delete the `.azure` folder from your workspace. Then, call `azd up` again and select a different region. 
* You may debug further using [azd commands](https://learn.microsoft.com/azure/developer/azure-developer-cli/reference#azd-deploy). `azd show` displays information abour your app and resources, and `azd deploy --debug` enables debugging and logging while deploying the application's code to Azure. 
* Ensure that your az and azd tools are up to date.
* After fully deploying with azd, additional errors in the Azure Portal may indicate that your latest code has not been successfully deployed

#### Azure Container Apps
* If your ACA does not boot up, it is possible that your deployment has failed. This could be due to quota constraints, permission issues, or resource availability. Check failures in the deployment and container app logs in the Azure Portal.
* Console traces in ACA can be found in the Azure Portal, but they may be unreliable. Use Python’s logging with INFO level, and adjust Azure HTTP logging to WARNING.
* Once your ACA is deployed, utilize the browser debugger (F12) and clear cache (CTRL+SHIFT+R). This can help debug the frontend for better traceability.

#### Agents
* If your agent is occasionally unresponsive, your model may have reached its rate limit. You can increase its quota by adjusting the bicep configuration or by editing the model in the Azure AI Foundry page for your project's model deployments. 
* If your agent is crashing, confirm that you are using a model that you have deployed to your project.
* For easier agents configuration and streamlined integration with an existing assistants library, export the agent from Azure AI Foundry and implement a yaml-based configuration. 
* This application is designed to serve multiple users on multiple browsers. This application uses cookies to ensure that the same thread is reused for conversations across multiple tabs in the same browser. If the browser is restarted, the old thread will continue to serve the user. However, if the application has a new agent after a server restart or a thread is deleted, a new thread will be created without requiring a browser refresh or signaling to the users. When users submit a message to the web server, the web server will create an agent, thread, and stream back a reply. The response contains `agent_id` and `thread_id` in cookies. As a result, each subsequent message sent to the web server will also contain these IDs. As long as the same agent is being used in the system and the thread can be retrieved in the cookie, the same thread will be used to serve the users.
* For document handling, use filename-based downloads to avoid storing files in dictionaries.
* Intermittent errors may arise when retrieving filenames for file IDs, which may be mitigated by using a single worker and fresh threads for each new assistant.
* File citation can be enhanced by automatically including filenames to reduce manual steps. 
