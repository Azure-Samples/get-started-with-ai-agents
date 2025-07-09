#!/bin/bash

set -e

# Check if already logged in
if ! az account show &>/dev/null; then
    echo -e "🔐 Not logged in to Azure. Attempting to login..."

    azureTenantId=$(azd env get-value AZURE_TENANT_ID)
    if [[ -z "$azureTenantId" ]]; then
        echo "❌ AZURE_TENANT_ID is not set in the environment. Exiting."
        exit 1
    fi

    az login --tenant "$azureTenantId" > /dev/null
    if [[ $? -ne 0 ]]; then
        echo "❌ Azure login failed. Exiting script."
        exit 1
    fi

    echo "✅ Logged in to Azure successfully."
else
    user=$(az account show --query user.name -o tsv)
    echo "✅ Already logged in as: $user"
fi

templateValidationMode="${TEMPLATE_VALIDATION_MODE}"

if [[ "$templateValidationMode" == true ]]; then
  username="user"
  password="pwd"
else
  # Prompt for username with validation
  while true; do
    read -rp "👤 Create a new username for the web app (no spaces, at least 1 character): " username

    if [[ -z "$username" || "$username" =~ [[:space:]] ]]; then
      echo "❌ Username cannot be empty or contain spaces." >&2
    else
      break
    fi
  done

  # Prompt for password with validation
  while true; do
    read -rsp "🔑 Create a new password for the web app (no spaces, at least 1 character): " password
    echo
    read -rsp "🔑 Confirm the new password: " confirmPassword
    echo

    if [[ -z "$password" ]]; then
      echo "❌ Password cannot be empty." >&2
    elif [[ "$password" != "$confirmPassword" ]]; then
      echo "❌ Passwords do not match." >&2
    elif [[ "$password" =~ [[:space:]] ]]; then
      echo "❌ Password cannot contain spaces." >&2
    else
      break
    fi
  done
fi

# Get resource group and container app name from azd
resourceGroupName=$(azd env get-value AZURE_RESOURCE_GROUP)
containerAppName=$(azd env get-value SERVICE_API_NAME)
subscriptionId=$(azd env get-value AZURE_SUBSCRIPTION_ID)

az account set --subscription $subscriptionId
echo "🎯 Active Subscription: $(az account show --query '[name, id]' --output tsv)"

echo "⏳ Setup username and password in the secrets..."

# Set the secrets
az containerapp secret set \
  --name "$containerAppName" \
  --resource-group "$resourceGroupName" \
  --secrets web-app-username="$username" web-app-password="$password" \
  > /dev/null 2>&1

#set the environment variables to reference the secrets
az containerapp update \
  --name "$containerAppName" \
  --resource-group "$resourceGroupName" \
  --set-env-vars WEB_APP_USERNAME=secretref:web-app-username WEB_APP_PASSWORD=secretref:web-app-password \
  > /dev/null 2>&1

echo "✅ New username and password now are in the secrets"
echo "🔍 Querying the active revision in the container app..."

# Get the active revision name
activeRevision=$(az containerapp revision list \
  --name "$containerAppName" \
  --resource-group "$resourceGroupName" \
  --query '[?properties.active==`true`].name' \
  --output tsv)

if [[ -z "$activeRevision" ]]; then
  echo "❌ No active revision found for the specified Container App." >&2
  exit 1
fi

echo "♻️ Restarting revision $activeRevision..."

# Restart the active revision
az containerapp revision restart \
  --name "$containerAppName" \
  --resource-group "$resourceGroupName" \
  --revision "$activeRevision" \
  > /dev/null 2>&1

echo "✅ Successfully restarted the revision: $activeRevision"

exit 0