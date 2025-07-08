# Define the .env file path
$envFilePath = "src\.env"

# Clear the contents of the .env file
Set-Content -Path $envFilePath -Value ""

# Append new values to the .env file
$aiProjectResourceId = azd env get-value AZURE_EXISTING_AIPROJECT_RESOURCE_ID 2>$null
$aiProjectEndpoint = azd env get-value AZURE_EXISTING_AIPROJECT_ENDPOINT 2>$null
$azureAiagentDeploymentName = azd env get-value AZURE_AI_AGENT_DEPLOYMENT_NAME 2>$null
$azureAiAgentId = azd env get-value AZURE_EXISTING_AGENT_ID 2>$null
$azureAiAgentName = azd env get-value AZURE_AI_AGENT_NAME 2>$null
$azureTenantId = azd env get-value AZURE_TENANT_ID 2>$null
$searchConnectionName = azd env get-value AZURE_AI_SEARCH_CONNECTION_NAME 2>$null
$azureAIEmbedDeploymentName = azd env get-value AZURE_AI_EMBED_DEPLOYMENT_NAME 2>$null
$azureAIEmbedDimensions = azd env get-value AZURE_AI_EMBED_DIMENSIONS 2>$null
$azureAISearchIndexName = azd env get-value AZURE_AI_SEARCH_INDEX_NAME 2>$null
$azureAISearchEndpoint = azd env get-value AZURE_AI_SEARCH_ENDPOINT 2>$null
$serviceAPIUri = azd env get-value SERVICE_API_URI 2>$null
$enableAzureMonitorTracing = azd env get-value ENABLE_AZURE_MONITOR_TRACING 2>$null
$azureTracingGenAIContentRecordingEnabled = azd env get-value AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED 2>$null

Add-Content -Path $envFilePath -Value "AZURE_EXISTING_AIPROJECT_RESOURCE_ID=$aiProjectResourceId"
Add-Content -Path $envFilePath -Value "AZURE_EXISTING_AIPROJECT_ENDPOINT=$aiProjectEndpoint"
Add-Content -Path $envFilePath -Value "AZURE_AI_AGENT_DEPLOYMENT_NAME=$azureAiagentDeploymentName"
Add-Content -Path $envFilePath -Value "AZURE_EXISTING_AGENT_ID=$azureAiAgentId"
Add-Content -Path $envFilePath -Value "AZURE_TENANT_ID=$azureTenantId"
Add-Content -Path $envFilePath -Value "AZURE_AI_SEARCH_CONNECTION_NAME=$searchConnectionName"
Add-Content -Path $envFilePath -Value "AZURE_AI_EMBED_DEPLOYMENT_NAME=$azureAIEmbedDeploymentName"
Add-Content -Path $envFilePath -Value "AZURE_AI_EMBED_DIMENSIONS=$azureAIEmbedDimensions"
Add-Content -Path $envFilePath -Value "AZURE_AI_SEARCH_INDEX_NAME=$azureAISearchIndexName"
Add-Content -Path $envFilePath -Value "AZURE_AI_SEARCH_ENDPOINT=$azureAISearchEndpoint"
Add-Content -Path $envFilePath -Value "AZURE_AI_AGENT_NAME=$azureAiAgentName"
Add-Content -Path $envFilePath -Value "AZURE_TENANT_ID=$azureTenantId"
Add-Content -Path $envFilePath -Value "ENABLE_AZURE_MONITOR_TRACING=$enableAzureMonitorTracing"
Add-Content -Path $envFilePath -Value "AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=$azureTracingGenAIContentRecordingEnabled"
