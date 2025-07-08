#!/bin/bash

# Define the .env file path
ENV_FILE_PATH="src/.env"

# Clear the contents of the .env file
> $ENV_FILE_PATH

echo "AZURE_EXISTING_AIPROJECT_RESOURCE_ID=$(azd env get-value AZURE_EXISTING_AIPROJECT_RESOURCE_ID 2>/dev/null)" >> $ENV_FILE_PATH
echo "AZURE_AI_AGENT_DEPLOYMENT_NAME=$(azd env get-value AZURE_AI_AGENT_DEPLOYMENT_NAME 2>/dev/null)" >> $ENV_FILE_PATH
echo "AZURE_EXISTING_AGENT_ID=$(azd env get-value AZURE_EXISTING_AGENT_ID 2>/dev/null)" >> $ENV_FILE_PATH
echo "AZURE_TENANT_ID=$(azd env get-value AZURE_TENANT_ID 2>/dev/null)" >> $ENV_FILE_PATH
echo "AZURE_AI_SEARCH_CONNECTION_NAME=$(azd env get-value AZURE_AI_SEARCH_CONNECTION_NAME 2>/dev/null)" >> $ENV_FILE_PATH
echo "AZURE_AI_EMBED_DEPLOYMENT_NAME=$(azd env get-value AZURE_AI_EMBED_DEPLOYMENT_NAME 2>/dev/null)" >> $ENV_FILE_PATH
echo "AZURE_AI_EMBED_DIMENSIONS=$(azd env get-value AZURE_AI_EMBED_DIMENSIONS 2>/dev/null)" >> $ENV_FILE_PATH
echo "AZURE_AI_SEARCH_INDEX_NAME=$(azd env get-value AZURE_AI_SEARCH_INDEX_NAME 2>/dev/null)" >> $ENV_FILE_PATH
echo "AZURE_AI_SEARCH_ENDPOINT=$(azd env get-value AZURE_AI_SEARCH_ENDPOINT 2>/dev/null)" >> $ENV_FILE_PATH
echo "AZURE_AI_AGENT_NAME=$(azd env get-value AZURE_AI_AGENT_NAME 2>/dev/null)" >> $ENV_FILE_PATH
echo "AZURE_TENANT_ID=$(azd env get-value AZURE_TENANT_ID 2>/dev/null)" >> $ENV_FILE_PATH
echo "AZURE_EXISTING_AIPROJECT_ENDPOINT=$(azd env get-value AZURE_EXISTING_AIPROJECT_ENDPOINT 2>/dev/null)" >> $ENV_FILE_PATH
echo "ENABLE_AZURE_MONITOR_TRACING=$(azd env get-value ENABLE_AZURE_MONITOR_TRACING 2>/dev/null)" >> $ENV_FILE_PATH
echo "AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=$(azd env get-value AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED 2>/dev/null)" >> $ENV_FILE_PATH

exit 0