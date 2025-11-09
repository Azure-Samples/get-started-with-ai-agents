# GitHub Actions Setup Guide

This guide will help you set up automated deployment to Azure using GitHub Actions.

## 📋 Prerequisites Completed ✅

- ✅ App Registration created
- ✅ Contributor role assigned to subscription
- ✅ App ID: `db57485e-6284-434d-ba83-e8fb848cc01d`
- ✅ Tenant ID: `b75007f5-364a-4c13-816e-74aacedc01a5`

---

## Step 1: Create Federated Credential

Run this command in **Azure Cloud Shell** or your local terminal (with Azure CLI):

```bash
az ad app federated-credential create \
  --id db57485e-6284-434d-ba83-e8fb848cc01d \
  --parameters '{
    "name": "Ksenia-personal-agent-main",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:Skie-Art/Ksenia-personal-agent:ref:refs/heads/main",
    "audiences": ["api://AzureADTokenExchange"],
    "description": "GitHub Actions deployment for main branch"
  }'
```

**Expected output:** Success message or "already exists" (both are fine)

---

## Step 2: Enable GitHub Actions

1. Go to: https://github.com/Skie-Art/Ksenia-personal-agent/actions
2. Click **"I understand my workflows, go ahead and enable them"**

---

## Step 3: Gather Your Azure Resource Information

You need to find these values from your Azure Portal:

### Option A: Use Azure Cloud Shell Script

Run the helper script from your Cloud Shell:
```bash
./scripts/setup_github_actions.sh
```

### Option B: Manually Gather Information

Go to **Azure Portal** → Your Resource Group and note down:

1. **AI Project name** (from AI Foundry)
2. **Resource Group name**
3. **Container Registry name**
4. **Storage Account name**
5. **Key Vault name**
6. **AI Services name**
7. **Agent ID** (from AI Foundry → Agents)

---

## Step 4: Set GitHub Repository Variables

Go to: https://github.com/Skie-Art/Ksenia-personal-agent/settings/variables/actions

Click **"New repository variable"** and add each variable below:

### Required Variables (Copy and fill in your values)

```
# Authentication
AZURE_CLIENT_ID = db57485e-6284-434d-ba83-e8fb848cc01d
AZURE_TENANT_ID = b75007f5-364a-4c13-816e-74aacedc01a5
AZURE_SUBSCRIPTION_ID = <YOUR_SUBSCRIPTION_ID>

# Environment
AZURE_ENV_NAME = prod
AZURE_LOCATION = <YOUR_REGION>  # e.g., eastus
AZURE_RESOURCE_GROUP = <YOUR_RESOURCE_GROUP>

# AI Resources
AZURE_AIPROJECT_NAME = <YOUR_AI_PROJECT_NAME>
AZURE_AISERVICES_NAME = <YOUR_AI_SERVICES_NAME>

# Infrastructure
AZURE_CONTAINER_REGISTRY_NAME = <YOUR_CONTAINER_REGISTRY>
AZURE_KEYVAULT_NAME = <YOUR_KEYVAULT_NAME>
AZURE_STORAGE_ACCOUNT_NAME = <YOUR_STORAGE_ACCOUNT>

# Configuration Flags
USE_CONTAINER_REGISTRY = true
USE_APPLICATION_INSIGHTS = false
USE_AZURE_AI_SEARCH_SERVICE = false

# Agent Configuration (GPT-5 mini!)
AZURE_AI_AGENT_NAME = agent-template-assistant
AZURE_EXISTING_AGENT_ID = <YOUR_AGENT_ID>
AZURE_AI_AGENT_DEPLOYMENT_NAME = gpt-5-mini
AZURE_AI_AGENT_MODEL_NAME = gpt-5-mini
AZURE_AI_AGENT_MODEL_FORMAT = OpenAI
AZURE_AI_AGENT_MODEL_VERSION = 2024-07-18
AZURE_AI_AGENT_DEPLOYMENT_SKU = GlobalStandard
AZURE_AI_AGENT_DEPLOYMENT_CAPACITY = 80

# Embedding Model
AZURE_AI_EMBED_DEPLOYMENT_NAME = text-embedding-3-small
AZURE_AI_EMBED_MODEL_NAME = text-embedding-3-small
AZURE_AI_EMBED_MODEL_FORMAT = OpenAI
AZURE_AI_EMBED_MODEL_VERSION = 1
AZURE_AI_EMBED_DEPLOYMENT_SKU = Standard
AZURE_AI_EMBED_DEPLOYMENT_CAPACITY = 50

# Existing Project
AZURE_EXISTING_AIPROJECT_RESOURCE_ID = <YOUR_PROJECT_RESOURCE_ID>
AZURE_EXISTING_AIPROJECT_ENDPOINT = <YOUR_PROJECT_ENDPOINT>
```

### Optional Variables (if using AI Search or App Insights)

```
# Optional: AI Search
AZURE_SEARCH_SERVICE_NAME = <YOUR_SEARCH_SERVICE>

# Optional: Monitoring
AZURE_APPLICATION_INSIGHTS_NAME = <YOUR_APP_INSIGHTS>
AZURE_LOG_ANALYTICS_WORKSPACE_NAME = <YOUR_LOG_ANALYTICS>
```

---

## Step 5: Test Your Deployment

1. Go to: https://github.com/Skie-Art/Ksenia-personal-agent/actions
2. Click on **"Deploy to Azure"** workflow
3. Click **"Run workflow"** → Select `main` branch → **"Run workflow"**
4. Watch the deployment progress!

---

## 🔍 How to Find Your Azure Resource Information

### Find Subscription ID:
```bash
az account show --query id -o tsv
```

Or in Portal: **Subscriptions** → Click your subscription → Copy **Subscription ID**

### Find AI Project Endpoint:
Portal: **AI Foundry** → Your Project → **Overview** → Copy **Project endpoint**

Format: `https://<project-name>.cognitiveservices.azure.com/`

### Find AI Project Resource ID:
Portal: **AI Foundry** → Your Project → **Properties** → Copy **Resource ID**

Format: `/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.MachineLearningServices/workspaces/<project-name>`

### Find Agent ID:
Portal: **AI Foundry** → Your Project → **Agents** → Click your agent → Copy **Agent ID**

---

## 🎯 What Each Workflow Does

### 1. `azure-dev.yml` - Main Deployment
- **Triggers:** Push to main OR manual run
- **Actions:**
  - Builds Docker container
  - Pushes to Azure Container Registry
  - Deploys to Azure Container Apps
  - Updates your agent application

### 2. `ai-evaluation.yaml` - Agent Testing
- **Triggers:** Push to main OR manual run
- **Actions:**
  - Runs automated evaluations on your agent
  - Tests quality, safety, and performance
  - Reports results

### 3. `template-validation.yml` - Infrastructure Validation
- **Triggers:** Manual run only
- **Actions:**
  - Validates Bicep templates
  - Checks infrastructure configuration

---

## 🚨 Troubleshooting

### Error: "No permission to access resource"
- Make sure the service principal has **Contributor** role on your subscription
- Verify in: Portal → Subscriptions → Access Control (IAM)

### Error: "Federated credential not found"
- Rerun the federated credential creation command from Step 1
- Wait 5-10 minutes for Azure to propagate the credential

### Error: "Resource not found"
- Double-check all your variable names match exactly
- Verify resources exist in the Azure Portal

### Workflow doesn't trigger
- Make sure workflows are enabled in your repo
- Check that you're pushing to the `main` branch

---

## ✅ Checklist

- [ ] Federated credential created (Step 1)
- [ ] GitHub Actions enabled (Step 2)
- [ ] All Azure resource information gathered (Step 3)
- [ ] All GitHub variables configured (Step 4)
- [ ] Test deployment run successfully (Step 5)

---

## 📚 Resources

- [Azure Federated Credentials](https://learn.microsoft.com/azure/developer/github/connect-from-azure)
- [GitHub Actions Variables](https://docs.github.com/en/actions/learn-github-actions/variables)
- [Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/)

---

**Need help?** Open an issue at: https://github.com/Skie-Art/Ksenia-personal-agent/issues
