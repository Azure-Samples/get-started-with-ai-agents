param name string
param location string = resourceGroup().location
param tags object = {}

param identityName string
param containerAppsEnvironmentName string
param projectConnectionString string
param agentDeploymentName string
param searchConnectionName string
param embeddingDeploymentName string
param aiSearchIndexName string
param embeddingDeploymentDimensions string
param searchServiceEndpoint string
param agentName string
param agentID string
param projectName string
param appConfigurationEndpoint string

resource apiIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
}

var env = [
  {
    name: 'AZURE_CLIENT_ID'
    value: apiIdentity.properties.clientId
  }
  {
    name: 'AZURE_AIPROJECT_CONNECTION_STRING'
    value: projectConnectionString
  }
  {
    name: 'AZURE_AI_AGENT_NAME'
    value: agentName
  }
  {
    name: 'AZURE_AI_AGENT_ID'
    value: agentID
  }
  {
    name: 'AZURE_AI_AGENT_DEPLOYMENT_NAME'
    value: agentDeploymentName
  }
  {
    name: 'AZURE_AI_EMBED_DEPLOYMENT_NAME'
    value: embeddingDeploymentName
  }
  {
    name: 'AZURE_AI_SEARCH_INDEX_NAME'
    value: aiSearchIndexName
  }
  {
    name: 'AZURE_AI_EMBED_DIMENSIONS'
    value: embeddingDeploymentDimensions
  }
  {
    name: 'RUNNING_IN_PRODUCTION'
    value: 'true'
  }
  {
    name: 'AZURE_AI_SEARCH_CONNECTION_NAME'
    value: searchConnectionName
  }
  {
    name: 'AZURE_AI_SEARCH_ENDPOINT'
    value: searchServiceEndpoint
  }
  {
    name: 'APP_CONFIGURATION_ENDPOINT'
    value: appConfigurationEndpoint
  }
]


module app 'core/host/container-app-upsert.bicep' = {
  name: 'container-app-module'
  params: {
    name: name
    location: location
    tags: tags
    identityName: apiIdentity.name
    containerAppsEnvironmentName: containerAppsEnvironmentName
    targetPort: 50505
    env: env
    projectName: projectName
  }
}

output SERVICE_API_IDENTITY_PRINCIPAL_ID string = apiIdentity.properties.principalId
output SERVICE_API_NAME string = app.outputs.name
output SERVICE_API_URI string = app.outputs.uri
