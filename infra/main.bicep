targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@description('Location for all resources')
// Based on the model, creating an agent is not supported in all regions. 
// The combination of allowed and usageName below is for AZD to check AI model gpt-4o-mini quota only for the allowed regions for creating an agent.
// If using different models, update the SKU,capacity depending on the model you use.
// https://learn.microsoft.com/azure/ai-services/agents/concepts/model-region-support
@allowed([
  'eastus'
  'eastus2'
  'swedencentral'
  'westus'
  'westus3'
])
@metadata({
  azd: {
    type: 'location'
    // quota-validation for ai models: gpt-4o-mini
    usageName: [
      'OpenAI.GlobalStandard.gpt-4o-mini,80'
    ]
  }
})
param location string

@description('Use this parameter to use an existing AI project resource ID')
param azureExistingAIProjectResourceId string = ''
@description('The Azure resource group where new resources will be deployed')
param resourceGroupName string = ''
@description('The Azure AI Foundry Hub resource name. If ommited will be generated')
param aiProjectName string = ''
@description('The application insights resource name. If ommited will be generated')
param applicationInsightsName string = ''
@description('The AI Services resource name. If ommited will be generated')
param aiServicesName string = ''
@description('The Azure Search resource name. If ommited will be generated')
param searchServiceName string = ''
@description('The Azure Search connection name. If ommited will use a default value')
param searchConnectionName string = ''
@description('The search index name')
param aiSearchIndexName string = ''
@description('The Azure Storage Account resource name. If ommited will be generated')
param storageAccountName string = ''
@description('The log analytics workspace name. If ommited will be generated')
param logAnalyticsWorkspaceName string = ''
@description('Id of the user or app to assign application roles')
param principalId string = ''

// Chat completion model
@description('Format of the chat model to deploy')
@allowed(['Microsoft', 'OpenAI'])
param agentModelFormat string = 'OpenAI'
@description('Name of agent to deploy')
param agentName string = 'agent-template-assistant'
@description('(Deprecated) ID of agent to deploy')
param aiAgentID string = ''
@description('ID of the existing agent')
param azureExistingAgentId string = ''
@description('Name of the chat model to deploy')
param agentModelName string = 'gpt-5-mini'
@description('Name of the model deployment')
param agentDeploymentName string = 'gpt-5-mini'

@description('Version of the chat model to deploy')
// See version availability in this table:
// https://learn.microsoft.com/azure/ai-services/openai/concepts/models#global-standard-model-availability
param agentModelVersion string = '2024-07-18'

@description('Sku of the chat deployment')
param agentDeploymentSku string = 'GlobalStandard'

@description('Capacity of the chat deployment')
// You can increase this, but capacity is limited per model/region, so you will get errors if you go over
// https://learn.microsoft.com/en-us/azure/ai-services/openai/quotas-limits
param agentDeploymentCapacity int = 30

// Embedding model
@description('Format of the embedding model to deploy')
@allowed(['Microsoft', 'OpenAI'])
param embedModelFormat string = 'OpenAI'

@description('Name of the embedding model to deploy')
param embedModelName string = 'text-embedding-3-small'
@description('Name of the embedding model deployment')
param embeddingDeploymentName string = 'text-embedding-3-small'
@description('Embedding model dimensionality')
param embeddingDeploymentDimensions string = '100'

@description('Version of the embedding model to deploy')
// See version availability in this table:
// https://learn.microsoft.com/azure/ai-services/openai/concepts/models#embeddings-models
param embedModelVersion string = '1'

@description('Sku of the embeddings model deployment')
param embedDeploymentSku string = 'Standard'

@description('Capacity of the embedding deployment')
// You can increase this, but capacity is limited per model/region, so you will get errors if you go over
// https://learn.microsoft.com/azure/ai-services/openai/quotas-limits
param embedDeploymentCapacity int = 30

param useApplicationInsights bool = true
@description('Do we want to use the Azure AI Search')
param useSearchService bool = false

@description('Do we want to use the Azure Monitor tracing')
param enableAzureMonitorTracing bool = false

@description('Do we want to use the Azure Monitor tracing for GenAI content recording')
param azureTracingGenAIContentRecordingEnabled bool = false

param templateValidationMode bool = false

@description('Random seed to be used during generation of new resources suffixes.')
param seed string = newGuid()

var runnerPrincipalType = templateValidationMode? 'ServicePrincipal' : 'User'

var abbrs = loadJsonContent('./abbreviations.json')

var resourceToken = templateValidationMode? toLower(uniqueString(subscription().id, environmentName, location, seed)) :  toLower(uniqueString(subscription().id, environmentName, location))

var tags = { 'azd-env-name': environmentName }

var tempAgentID = !empty(aiAgentID) ? aiAgentID : ''
var agentID = !empty(azureExistingAgentId) ? azureExistingAgentId : tempAgentID

var aiChatModel = [
  {
    name: agentDeploymentName
    model: {
      format: agentModelFormat
      name: agentModelName
      version: agentModelVersion
    }
    sku: {
      name: agentDeploymentSku
      capacity: agentDeploymentCapacity
    }
  }
]
var aiEmbeddingModel = [ 
  {
    name: embeddingDeploymentName
    model: {
      format: embedModelFormat
      name: embedModelName
      version: embedModelVersion
    }
    sku: {
      name: embedDeploymentSku
      capacity: embedDeploymentCapacity
    }
  }
]

var aiDeployments = concat(
  aiChatModel,
  useSearchService ? aiEmbeddingModel : [])


// Organize resources in a resource group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: !empty(resourceGroupName) ? resourceGroupName : '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

var logAnalyticsWorkspaceResolvedName = !useApplicationInsights
  ? ''
  : !empty(logAnalyticsWorkspaceName)
      ? logAnalyticsWorkspaceName
      : '${abbrs.operationalInsightsWorkspaces}${resourceToken}'

var resolvedSearchServiceName = !useSearchService
  ? ''
  : !empty(searchServiceName) ? searchServiceName : '${abbrs.searchSearchServices}${resourceToken}'
  

module ai 'core/host/ai-environment.bicep' = if (empty(azureExistingAIProjectResourceId)) {
  name: 'ai'
  scope: rg
  params: {
    location: location
    tags: tags
    storageAccountName: !empty(storageAccountName)
      ? storageAccountName
      : '${abbrs.storageStorageAccounts}${resourceToken}'
    aiServicesName: !empty(aiServicesName) ? aiServicesName : 'aoai-${resourceToken}'
    aiProjectName: !empty(aiProjectName) ? aiProjectName : 'proj-${resourceToken}'
    aiServiceModelDeployments: aiDeployments
    logAnalyticsName: logAnalyticsWorkspaceResolvedName
    applicationInsightsName: !useApplicationInsights
      ? ''
      : !empty(applicationInsightsName) ? applicationInsightsName : '${abbrs.insightsComponents}${resourceToken}'
    searchServiceName: resolvedSearchServiceName
    appInsightConnectionName: 'appinsights-connection'
    aoaiConnectionName: 'aoai-connection'
  }
}

var searchServiceEndpoint = !useSearchService
  ? ''
  : empty(azureExistingAIProjectResourceId) ? ai!.outputs.searchServiceEndpoint : ''

// If bringing an existing AI project, set up the log analytics workspace here
module logAnalytics 'core/monitor/loganalytics.bicep' = if (!empty(azureExistingAIProjectResourceId)) {
  name: 'logAnalytics'
  scope: rg
  params: {
    location: location
    tags: tags
    name: logAnalyticsWorkspaceResolvedName
  }
}
var existingProjEndpoint = !empty(azureExistingAIProjectResourceId) ? format('https://{0}.services.ai.azure.com/api/projects/{1}',split(azureExistingAIProjectResourceId, '/')[8], split(azureExistingAIProjectResourceId, '/')[10]) : ''

var projectResourceId = !empty(azureExistingAIProjectResourceId)
  ? azureExistingAIProjectResourceId
  : ai!.outputs.projectResourceId

var projectEndpoint = !empty(azureExistingAIProjectResourceId)
  ? existingProjEndpoint
  : ai!.outputs.aiProjectEndpoint

var resolvedApplicationInsightsName = !useApplicationInsights || !empty(azureExistingAIProjectResourceId)
  ? ''
  : !empty(applicationInsightsName) ? applicationInsightsName : '${abbrs.insightsComponents}${resourceToken}'

module monitoringMetricsContribuitorRoleAzureAIDeveloperRG 'core/security/appinsights-access.bicep' = if (!empty(resolvedApplicationInsightsName)) {
  name: 'monitoringmetricscontributor-role-azureai-developer-rg'
  scope: rg
  params: {
    principalType: 'ServicePrincipal'
    appInsightsName: resolvedApplicationInsightsName
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
  }
}

resource existingProjectRG 'Microsoft.Resources/resourceGroups@2021-04-01' existing = if (!empty(azureExistingAIProjectResourceId) && contains(azureExistingAIProjectResourceId, '/')) {
  name: split(azureExistingAIProjectResourceId, '/')[4]
}

module userRoleAzureAIDeveloperBackendExistingProjectRG 'core/security/role.bicep' = if (!empty(azureExistingAIProjectResourceId)) {
  name: 'backend-role-azureai-developer-existing-project-rg'
  scope: existingProjectRG
  params: {
    principalType: 'ServicePrincipal'
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: '64702f94-c441-49e6-a78b-ef80e0188fee' 
  }
}

//Container apps host and api
// Container apps host (including container registry)
module containerApps 'core/host/container-apps.bicep' = {
  name: 'container-apps'
  scope: rg
  params: {
    name: 'app'
    location: location
    containerRegistryName: '${abbrs.containerRegistryRegistries}${resourceToken}'
    tags: tags
    containerAppsEnvironmentName: 'containerapps-env-${resourceToken}'
    logAnalyticsWorkspaceName: empty(azureExistingAIProjectResourceId)
      ? ai!.outputs.logAnalyticsWorkspaceName
      : logAnalytics!.outputs.name
  }
}

// API app
module api 'api.bicep' = {
  name: 'api'
  scope: rg
  params: {
    name: 'ca-api-${resourceToken}'
    location: location
    tags: tags
    identityName: '${abbrs.managedIdentityUserAssignedIdentities}api-${resourceToken}'
    containerAppsEnvironmentName: containerApps.outputs.environmentName
    azureExistingAIProjectResourceId: projectResourceId
    containerRegistryName: containerApps.outputs.registryName
    agentDeploymentName: agentDeploymentName
    searchConnectionName: searchConnectionName
    aiSearchIndexName: aiSearchIndexName
    searchServiceEndpoint: searchServiceEndpoint
    embeddingDeploymentName: embeddingDeploymentName
    embeddingDeploymentDimensions: embeddingDeploymentDimensions
    agentName: agentName
    agentID: agentID
    enableAzureMonitorTracing: enableAzureMonitorTracing
    azureTracingGenAIContentRecordingEnabled: azureTracingGenAIContentRecordingEnabled
    projectEndpoint: projectEndpoint
  }
}



module userRoleAzureAIDeveloper 'core/security/role.bicep' = {
  name: 'user-role-azureai-developer'
  scope: rg
  params: {
    principalType: runnerPrincipalType
    principalId: principalId
    roleDefinitionId: '64702f94-c441-49e6-a78b-ef80e0188fee'
  }
}

module userCognitiveServicesUser  'core/security/role.bicep' = if (empty(azureExistingAIProjectResourceId)) {
  name: 'user-role-cognitive-services-user'
  scope: rg
  params: {
    principalType: runnerPrincipalType
    principalId: principalId
    roleDefinitionId: 'a97b65f3-24c7-4388-baec-2e87135dc908'
  }
}

module userAzureAIUser  'core/security/role.bicep' = if (empty(azureExistingAIProjectResourceId)) {
  name: 'user-role-azure-ai-user'
  scope: rg
  params: {
    principalType: runnerPrincipalType
    principalId: principalId
    roleDefinitionId: '53ca6127-db72-4b80-b1b0-d745d6d5456d'
  }
}

module backendCognitiveServicesUser  'core/security/role.bicep' = if (empty(azureExistingAIProjectResourceId)) {
  name: 'backend-role-cognitive-services-user'
  scope: rg
  params: {
    principalType: 'ServicePrincipal'
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: 'a97b65f3-24c7-4388-baec-2e87135dc908'
  }
}

module backendCognitiveServicesUser2  'core/security/role.bicep' = if (!empty(azureExistingAIProjectResourceId)) {
  name: 'backend-role-cognitive-services-user2'
  scope: existingProjectRG
  params: {
    principalType: 'ServicePrincipal'
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: 'a97b65f3-24c7-4388-baec-2e87135dc908'
  }
}


module backendRoleSearchIndexDataContributorRG 'core/security/role.bicep' = if (useSearchService) {
  name: 'backend-role-azure-index-data-contributor-rg'
  scope: rg
  params: {
    principalType: 'ServicePrincipal'
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
  }
}

module backendRoleSearchIndexDataReaderRG 'core/security/role.bicep' = if (useSearchService) {
  name: 'backend-role-azure-index-data-reader-rg'
  scope: rg
  params: {
    principalType: 'ServicePrincipal'
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
  }
}

module backendRoleSearchServiceContributorRG 'core/security/role.bicep' = if (useSearchService) {
  name: 'backend-role-azure-search-service-contributor-rg'
  scope: rg
  params: {
    principalType: 'ServicePrincipal'
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
  }
}

module userRoleSearchIndexDataContributorRG 'core/security/role.bicep' = if (useSearchService) {
  name: 'user-role-azure-index-data-contributor-rg'
  scope: rg
  params: {
    principalType: runnerPrincipalType
    principalId: principalId
    roleDefinitionId: '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
  }
}

module userRoleSearchIndexDataReaderRG 'core/security/role.bicep' = if (useSearchService) {
  name: 'user-role-azure-index-data-reader-rg'
  scope: rg
  params: {
    principalType: runnerPrincipalType
    principalId: principalId
    roleDefinitionId: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
  }
}

module userRoleSearchServiceContributorRG 'core/security/role.bicep' = if (useSearchService) {
  name: 'user-role-azure-search-service-contributor-rg'
  scope: rg
  params: {
    principalType: runnerPrincipalType
    principalId: principalId
    roleDefinitionId: '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
  }
}

module backendRoleAzureAIDeveloperRG 'core/security/role.bicep' = {
  name: 'backend-role-azureai-developer-rg'
  scope: rg
  params: {
    principalType: 'ServicePrincipal'
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: '64702f94-c441-49e6-a78b-ef80e0188fee'
  }
}

output AZURE_RESOURCE_GROUP string = rg.name

// Outputs required for local development server
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_EXISTING_AIPROJECT_RESOURCE_ID string = projectResourceId
output AZURE_AI_AGENT_DEPLOYMENT_NAME string = agentDeploymentName
output AZURE_AI_SEARCH_CONNECTION_NAME string = searchConnectionName
output AZURE_AI_EMBED_DEPLOYMENT_NAME string = embeddingDeploymentName
output AZURE_AI_SEARCH_INDEX_NAME string = aiSearchIndexName
output AZURE_AI_SEARCH_ENDPOINT string = searchServiceEndpoint
output AZURE_AI_EMBED_DIMENSIONS string = embeddingDeploymentDimensions
output AZURE_AI_AGENT_NAME string = agentName
output AZURE_EXISTING_AGENT_ID string = agentID
output AZURE_EXISTING_AIPROJECT_ENDPOINT string = projectEndpoint
output ENABLE_AZURE_MONITOR_TRACING bool = enableAzureMonitorTracing
output AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED bool = azureTracingGenAIContentRecordingEnabled

// Outputs required by azd for ACA
output AZURE_CONTAINER_ENVIRONMENT_NAME string = containerApps.outputs.environmentName
output SERVICE_API_IDENTITY_PRINCIPAL_ID string = api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
output SERVICE_API_NAME string = api.outputs.SERVICE_API_NAME
output SERVICE_API_URI string = api.outputs.SERVICE_API_URI
output SERVICE_API_ENDPOINTS array = ['${api.outputs.SERVICE_API_URI}']
output SEARCH_CONNECTION_ID string = ''
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerApps.outputs.registryLoginServer
