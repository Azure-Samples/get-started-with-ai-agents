# Define the .env file path
$envFilePath = "src\.env"

# Clear the contents of the .env file
Set-Content -Path $envFilePath -Value ""

# Append new values to the .env file
$aiProjectResourceId = azd env get-value AZURE_EXISTING_AIPROJECT_RESOURCE_ID
$aiProjectEndpoint = azd env get-value AZURE_EXISTING_AIPROJECT_ENDPOINT
$azureAiagentDeploymentName = azd env get-value AZURE_AI_AGENT_DEPLOYMENT_NAME
$azureAiAgentId = azd env get-value AZURE_EXISTING_AGENT_ID
$azureAiAgentName = azd env get-value AZURE_AI_AGENT_NAME
$azureTenantId = azd env get-value AZURE_TENANT_ID
$searchConnectionName = azd env get-value AZURE_AI_SEARCH_CONNECTION_NAME
$azureAIEmbedDeploymentName = azd env get-value AZURE_AI_EMBED_DEPLOYMENT_NAME
$azureAIEmbedDimensions = azd env get-value AZURE_AI_EMBED_DIMENSIONS
$azureAISearchIndexName = azd env get-value AZURE_AI_SEARCH_INDEX_NAME
$azureAISearchEndpoint = azd env get-value AZURE_AI_SEARCH_ENDPOINT
$serviceAPIUri = azd env get-value SERVICE_API_URI
$enableAzureMonitorTracing = azd env get-value ENABLE_AZURE_MONITOR_TRACING
$azureTracingGenAIContentRecordingEnabled = azd env get-value AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED

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

Write-Host "Web app URL:"
Write-Host $serviceAPIUri -ForegroundColor Cyan