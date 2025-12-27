# Deployment Guide

## Prerequisites

If you do not have an Azure Subscription, you can sign up for a [free Azure account](https://azure.microsoft.com/free/) and create an Azure Subscription.

To deploy this Azure environment successfully, your Azure account (the account you authenticate with) must have the following permissions and prerequisites on the targeted Azure Subscription:

- **Microsoft.Authorization/roleAssignments/write** permissions at the subscription scope.  
  _(typically included if you have [Role Based Access Control Administrator](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles#role-based-access-control-administrator-preview), [User Access Administrator](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles#user-access-administrator), or [Owner](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles#owner) role)_
- **Microsoft.Resources/deployments/write** permissions at the subscription scope.

You can view the permissions for your account and subscription by going to Azure portal, clicking 'Subscriptions' under 'Navigation' and then choosing your subscription from the list. If cannot find the subscription, make sure no filters are selected. After selecting your subscription, select 'Access control (IAM)' and you can see the roles that are assigned to your account for this subscription. To get more information about the roles, go to the 'Role assignments' tab, search by your account name and click the role you want to view more information about.

Check the [Azure Products by Region](https://azure.microsoft.com/explore/global-infrastructure/products-by-region/?products=all&regions=all) page and select a **region** where the following services are available:

- [Microsoft Foundry](https://learn.microsoft.com/azure/ai-foundry/)
- [Azure Container Apps](https://learn.microsoft.com/azure/container-apps/)
- [Azure Container Registry](https://learn.microsoft.com/azure/container-registry/)
- [Azure AI Search](https://learn.microsoft.com/azure/search/)
- [GPT Model Capacity](https://learn.microsoft.com/azure/ai-services/openai/concepts/models)

Here are some examples of the regions where the services are available: East US, East US2, Japan East, UK South, Sweden Central.

### Install and verify the Bicep CLI

`azd up` compiles every file under `infra/*.bicep`. To avoid network downloads during deployment, make sure the Bicep CLI is already available on your machine (or Codespace) through the Azure CLI:

```bash
az bicep install   # or az bicep upgrade
az bicep version   # verify installation
```

If you prefer to use the standalone `bicep` binary, place it on your `PATH` before running `azd up`.


### **Important Note for PowerShell Users**

If you encounter issues running PowerShell scripts due to the policy of not being digitally signed, you can temporarily adjust the `ExecutionPolicy` by running the following command in an elevated PowerShell session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

This will allow the scripts to run for the current session without permanently changing your system's policy.

## Deployment Options & Steps

### Deployment Steps 

Pick from the options below to see step-by-step instructions for GitHub Codespaces, VS Code Dev Containers, Local Environments, and Bicep deployments.

| [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new/Azure-Samples/get-started-with-ai-agents) | [![Open in Dev Containers](https://img.shields.io/static/v1?style=for-the-badge&label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/Azure-Samples/get-started-with-ai-agents) |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

<details>
  <summary><b>Deploy in GitHub Codespaces</b></summary>

### GitHub Codespaces

You can run this template virtually by using GitHub Codespaces. The button will open a web-based VS Code instance in your browser:

1. Open the template (this may take several minutes):

    [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/Azure-Samples/get-started-with-ai-agents)

2. Open a terminal window
3. Continue with the [deploying steps](#deploying-with-azd)

</details>

<details>
  <summary><b>Deploy in VS Code</b></summary>

### VS Code Dev Containers

A related option is VS Code Dev Containers, which will open the project in your local VS Code using the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers):

1. Start Docker Desktop (install it if not already installed [Docker Desktop](https://www.docker.com/products/docker-desktop/))
2. Open the project:

    [![Open in Dev Containers](https://img.shields.io/static/v1?style=for-the-badge&label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/Azure-Samples/get-started-with-ai-agents)

3. In the VS Code window that opens, once the project files show up (this may take several minutes), open a terminal window.
4. Continue with the [deploying steps](#deploying-with-azd).

</details>

<details>
  <summary><b>Deploy in your local Environment</b></summary>

### Local Environment

If you're not using one of the above options for opening the project, then you'll need to:

1. Make sure the following tools are installed:

   - [Azure Developer CLI (azd)](https://aka.ms/install-azd) Install or update to the latest version. Instructions can be found on the linked page.
   - [Python 3.9+](https://www.python.org/downloads/)
   - [Git](https://git-scm.com/downloads)
   - \[Windows Only\] [PowerShell](https://learn.microsoft.com/powershell/scripting/install/installing-powershell-on-windows) of the latest version, needed only for local application development on Windows operation system. Please make sure that path to power shell executable `pwsh.exe` is added to the `PATH` variable.

2. Clone the repository or download the project code via command-line:

   ```shell
   azd init -t get-started-with-ai-agents
   ```

3. Open the project folder in your terminal or editor.
4. Continue with the [deploying steps](#deploying-with-azd).

</details>

<details>
  <summary><b>Develop with Local Development Server</b></summary>

### Develop with Local Development Server

You can optionally use a local development server to test app changes locally. Make sure you first [deployed the app](#deploying-with-azd) to Azure before running the development server.

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

4. Install [Node.js](https://nodejs.org/) (v20 or later).
   
5. Install [pnpm](https://pnpm.io/installation)

6. Navigate to the frontend directory and setup for React UI:

    ```shell
    cd src/frontend
    pnpm run setup
    ```

7. Fill in the environment variables in `.env`.

9. (Optional) if you have changes in `src/frontend`, execute:

    ```shell
    pnpm build
    ```

    The build output will be placed in the `../api/static/react` directory, where the backend can serve it.

10. (Optional) If you have changes in `gunicorn.conf.py`, execute:

    ```shell
    python gunicorn.conf.py    
    ```

11. Run the local server:

    ```shell
    python -m uvicorn "api.main:create_app" --factory --reload
    ```

12. Click '<http://127.0.0.1:8000>' in the terminal, which should open a new tab in the browser.

13. Enter your message in the box.

</details>

<br/>

Consider the following settings during deployment:

<details>
  <summary><b>Configurable Deployment Settings</b></summary>

When you start a deployment, most parameters will have default values. You can change the following default settings:

| **Setting** | **Description** |  **Default value** |
|------------|----------------|  ------------|
| **Existing Project Resource ID** | Specify an existing project resource ID to be used instead of provisioning new Microsoft Foundry project and Foundry Tools. |   |
| **Azure Region** | Select a region with quota which supports your selected model. |   |
| **Model** | Choose from the [list of models supported by Foundry Agent Service](https://learn.microsoft.com/azure/ai-services/agents/concepts/model-region-support) for your selected region. | gpt-5-mini |  
| **Model Format** | Choose from OpenAI or Microsoft, depending on your model. | OpenAI |  
| **Model Deployment Capacity** | Configure capacity for your model. | 80k |
| **Embedding Model** | Choose from text-embedding-3-large, azdtext-embedding-3-small, and text-embedding-ada-002. This may only be deployed if Azure AI Search is enabled. |  text-embedding-3-small |
| **Embedding Model Capacity** | Configure capacity for your embedding model. |  50k |
| **Knowledge Retrieval** | Choose OpenAI's file search or Azure AI Search Index. |  OpenAI's file search |

For a detailed description of customizable fields and instructions, view the [deployment customization guide](deploy_customization.md).


</details>

<details>
  <summary><b>Configurable Agents Knowledge Retrieval</b></summary>

### Configurable Agents Knowledge Retrieval

By default, the template deploys OpenAI's [file search](https://learn.microsoft.com/azure/ai-services/agents/how-to/tools/file-search?tabs=python&pivots=overview) for agent's knowledge retrieval. An agent also can perform search using the search index, deployed in Azure AI Search resource. The semantic index search represents so-called hybrid search i.e. it uses LLM to search for the relevant context in the provided index as well as embedding similarity search. This index is built from the `embeddings.csv` file, containing the embeddings vectors, followed by the contexts.
To use index search, please set the local environment variable `USE_AZURE_AI_SEARCH_SERVICE` to `true` during the `azd up` command. In this case the Azure AI Search resource will be deployed and used. For more information on Azure AI serach, please see the [Azure AI Search Setup Guide](ai_search.md)

To specify the model (e.g. gpt-5-mini, gpt-5) that is deployed for the agent when `azd up` is called, set the following environment variables:

```shell
azd env set AZURE_AI_AGENT_MODEL_NAME <MODEL_NAME>
azd env set AZURE_AI_AGENT_MODEL_VERSION <MODEL_VERSION>
```
</details>

<details>
 <summary><b>Configure Tracing and Azure Monitor</b></summary>
To enable tracing for AI Agent to Azure Monitor, set the following environment variable:

```shell
azd env set ENABLE_AZURE_MONITOR_TRACING true
```

To enable message contents to be included in the traces, set the following environment variable. Note that the messages may contain personally identifiable information.

```shell
azd env set OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT true
```

You can view the App Insights tracing in Microsoft Foundry. Select your project on the Microsoft Foundry page and then click 'Tracing'.

</details>

<details>
  <summary><b>Quota Recommendations</b></summary>

### Quota Recommendations

The default for the model capacity in deployment is 80k tokens for chat model and 50k for embedded model for AI Search. For optimal performance, it is recommended to increase to 100k tokens. You can change the capacity by following the steps in [setting capacity and deployment SKU](deploy_customization.md#customizing-model-deployments).

- Navigate to [Monitor and track your quota usage](https://ai.azure.com/managementCenter/quota)
* In the Quota tab, click the GlobalStandard dropdown and select the model and region you are using for this accelerator to see your available quota. Please note gpt-5-mini and text-embedding-3-small are used as default.
- Request more quota or delete any unused model deployments as needed.

</details>


### Deploying with AZD

Once you've opened the project in [Codespaces](#github-codespaces) or in [Dev Containers](#vs-code-dev-containers) or [locally](#local-environment), you can deploy it to Azure following the following steps.

1. (Optional) If you would like to customize the deployment to [disable resources](deploy_customization.md#enabling-and-disabling-resources-provision), [customize resource names](deploy_customization.md#customizing-resource-names), [customize the models](deploy_customization.md#customizing-model-deployments) or [increase quota](deploy_customization.md#setting-models-capacity-and-deployment-sku), you can follow those steps now.

    ⚠️ **NOTE!** For optimal performance, the recommended quota is 100k tokens per minute. If you have the capacity, we recommend increasing the quota by running the following command:

    ```shell
    azd env set AZURE_AI_AGENT_DEPLOYMENT_CAPACITY 100
    ```

    ⚠️ If you do not increase your quota, you may encounter rate limit issues. If needed, you can increase the quota after deployment by editing your model in the Models and Endpoints tab of the [Microsoft Foundry Portal](https://ai.azure.com/).

2. Provision resources, build a docker image using `src` folder, and deploy:

    ```shell
    azd up
    ```

3. You will be prompted to provide an `azd` environment name (like "azureaiapp"), select a subscription from your Azure account, and select a location which has quota for all the resources. Then, it will provision the resources in your account and deploy the latest code.

    - For guidance on selecting a region with quota and model availability, follow the instructions in the [quota recommendations](#quota-recommendations) section and ensure that your model is available in your selected region by checking the [list of models supported by Foundry Agent Service](https://learn.microsoft.com/azure/ai-services/agents/concepts/model-region-support)
    - This deployment will take 7-10 minutes to provision the resources in your account and set up the solution with sample data.
    - If you get an error or timeout with deployment, changing the location can help, as there may be availability constraints for the resources. You can do this by running `azd down` and deleting the `.azure` folder from your code, and then running `azd up` again and selecting a new region.

    **NOTE!** If you get authorization failed and/or permission related errors during the deployment, please refer to the Azure account requirements in the [Prerequisites](#prerequisites) section. If you were recently granted these permissions, it may take a few minutes for the authorization to apply.

4. When `azd` has finished deploying, you'll see an endpoint URI in the command output. Visit that URI, and you should see the app! 🎉

    - From here, you can interact with the agent. Try chatting with the agent by asking for a joke, or you could try a more specific query to see the agent's citation capabilities. By default, this solution uploads two documents from the `src/files` folder. To see the agent use this information, try asking about Contoso's products.

    - You can view information about your deployment with:

        ```shell
        azd show
        ```

5. (Optional) Now that your app has deployed, you can view your resources in the Azure Portal and your deployments in Microsoft Foundry.
    - In the [Azure Portal](https://portal.azure.com/), navigate to your environment's resource group. The name will be `rg-[your environment name]`. Here, you should see your container app, storage account, and all of the other [resources](#resources) that are created in the deployment.
    - In the [Microsoft Foundry Portal](https://ai.azure.com/), select your project. If you navigate to the Agents tab, you should be able to view your new agent, named `agent-template-assistant`. If you navigate to the Models and Endpoints tab, you should see your AI Services connection with your model deployments.

6. (Optional) You can use a local development server to test app changes locally. To do so, follow the steps in [local deployment server](#develop-with-local-development-server) after your app is deployed.

7. (Optional) To redeploy, run `azd deploy`.  This will cause new docker image rebuilt, push to Azure Container Registry, and a new revision in Azure Container App with a new docker image.

This will rebuild the source code, package it into a container, and push it to the Azure Container Registry associated with your deployment.

This guide provides step-by-step instructions for deploying your application using Azure Container Registry (ACR) and Azure Container Apps.

There are several ways to deploy the solution. You can deploy to run in Azure in one click, or manually, or you can deploy locally.

When Deployment is complete, follow steps in [Set Up Authentication in Azure App Service](azure_app_service_auth_setup.md) to add app authentication with AAD to your web app running on Azure App Service.  Alternatively, run `./scripts/setup_credential.ps1` or `./scripts/setup_credential.sh` to setup basic auth with username and password.

