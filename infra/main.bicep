targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@minLength(1)
@description('Location for all resources')
// Look for desired models on the availability table:
// Agents must be supported in the region
// https://learn.microsoft.com/azure/ai-services/agents/concepts/model-region-support
@allowed([
  'eastus'
  'eastus2'
  'swedencentral'
  'switzerlandnorth'
  'westus'
  'westus3'
])
@metadata({
  azd: {
    type: 'location'
  }
})
param location string

@description('Use this parameter to use an existing AI project connection string')
param aiExistingProjectConnectionString string = ''
@description('The Azure resource group where new resources will be deployed')
param resourceGroupName string = ''
@description('The Azure AI Foundry Hub resource name. If ommited will be generated')
param aiHubName string = ''
@description('The Azure AI Foundry project name. If ommited will be generated')
param aiProjectName string = ''
@description('The application insights resource name. If ommited will be generated')
param applicationInsightsName string = ''
@description('The AI Services resource name. If ommited will be generated')
param aiServicesName string = ''
@description('The AI Services connection name. If ommited will use a default value')
param aiServicesConnectionName string = ''
@description('The Azure Key Vault resource name. If ommited will be generated')
param keyVaultName string = ''
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

// Chat completion model
@description('Format of the chat model to deploy')
@allowed(['Microsoft', 'OpenAI'])
param agentModelFormat string = 'OpenAI'
@description('Name of agent to deploy')
param agentName string = 'agent-template-assistant'
@description('ID of agent to deploy')
param aiAgentID string = ''
@description('Name of the chat model to deploy')
param agentModelName string = 'gpt-4o-mini'
@description('Name of the model deployment')
param agentDeploymentName string = 'gpt-4o-mini'

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
@secure()
param embedModelVersion string = '1'

@description('Sku of the embeddings model deployment')
param embedDeploymentSku string = 'Standard'

@description('Capacity of the embedding deployment')
// You can increase this, but capacity is limited per model/region, so you will get errors if you go over
// https://learn.microsoft.com/azure/ai-services/openai/quotas-limits
param embedDeploymentCapacity int = 30

@description('Do we want to use Azure Application Insights')
param useApplicationInsights bool = true

@description('Do we want to use Azure App Configuration')
param useAppConfiguration bool = true

@description('Do we want to use Azure App Configuration')
param appConfigurationSku string = 'free' 

@description('Do we want to use the Azure AI Search')
param useSearchService bool = false

@description('Id of the user or app to assign application roles')
param principalId string = ''

@description('Random seed to be used during generation of new resources suffixes.')
param seed string = newGuid() // why do we need this?

var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location, seed))
var projectName = !empty(aiProjectName) ? aiProjectName : 'ai-project-${resourceToken}'
var tags = { 'azd-env-name': environmentName }

var agentID = !empty(aiAgentID) ? aiAgentID : ''

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

module ai 'core/host/ai-environment.bicep' = if (empty(aiExistingProjectConnectionString)) {
  name: 'ai'
  scope: rg
  params: {
    location: location
    tags: tags
    hubName: !empty(aiHubName) ? aiHubName : 'ai-hub-${resourceToken}'
    projectName: projectName
    keyVaultName: !empty(keyVaultName) ? keyVaultName : '${abbrs.keyVaultVaults}${resourceToken}'
    storageAccountName: !empty(storageAccountName)
      ? storageAccountName
      : '${abbrs.storageStorageAccounts}${resourceToken}'
    aiServicesName: !empty(aiServicesName) ? aiServicesName : 'aoai-${resourceToken}'
    aiServicesConnectionName: !empty(aiServicesConnectionName) ? aiServicesConnectionName : 'aoai-${resourceToken}'
    aiServiceModelDeployments: aiDeployments
    logAnalyticsName: logAnalyticsWorkspaceResolvedName
    applicationInsightsName: !useApplicationInsights
      ? ''
      : !empty(applicationInsightsName) ? applicationInsightsName : '${abbrs.insightsComponents}${resourceToken}'
    searchServiceName: resolvedSearchServiceName
    searchConnectionName: !useSearchService
      ? ''
      : !empty(searchConnectionName) ? searchConnectionName : 'search-service-connection'
  }
}

var searchServiceEndpoint = !useSearchService
  ? ''
  : ai.outputs.searchServiceEndpoint

// If bringing an existing AI project, set up the log analytics workspace here
module logAnalytics 'core/monitor/loganalytics.bicep' = if (!empty(aiExistingProjectConnectionString)) {
  name: 'logAnalytics'
  scope: rg
  params: {
    location: location
    tags: tags
    name: logAnalyticsWorkspaceResolvedName
  }
}

var hostName = empty(aiExistingProjectConnectionString) && !empty(ai.outputs.discoveryUrl) && contains(ai.outputs.discoveryUrl, '/') ? split(ai.outputs.discoveryUrl, '/')[2] : ''
var projectConnectionString = empty(hostName)
  ? aiExistingProjectConnectionString
  : '${hostName};${subscription().subscriptionId};${rg.name};${projectName}'

var resolvedApplicationInsightsName = !useApplicationInsights || !empty(aiExistingProjectConnectionString)
  ? ''
  : !empty(applicationInsightsName) ? applicationInsightsName : '${abbrs.insightsComponents}${resourceToken}'

module monitoringMetricsContribuitorRoleAzureAIDeveloperRG 'core/security/appinsights-access.bicep' = if (!empty(resolvedApplicationInsightsName)) {
  name: 'monitoringmetricscontributor-role-azureai-developer-rg'
  scope: rg
  params: {
    appInsightsName: resolvedApplicationInsightsName
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
  }
}

resource existingProjectRG 'Microsoft.Resources/resourceGroups@2021-04-01' existing = if (!empty(aiExistingProjectConnectionString) && contains(aiExistingProjectConnectionString, ';')) {
  name: split(aiExistingProjectConnectionString, ';')[2]
}

module userRoleAzureAIDeveloperBackendExistingProjectRG 'core/security/role.bicep' = if (!empty(aiExistingProjectConnectionString)) {
  name: 'backend-role-azureai-developer-existing-project-rg'
  scope: existingProjectRG
  params: {
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
    tags: tags
    containerAppsEnvironmentName: 'containerapps-env-${resourceToken}'
    logAnalyticsWorkspaceName: empty(aiExistingProjectConnectionString)
      ? ai.outputs.logAnalyticsWorkspaceName
      : logAnalytics.outputs.name
  }
}

// App Configuration
module configStore 'core/config/configstore.bicep' = if (useApplicationInsights && useAppConfiguration) {
  name: 'config-store'
  scope: rg
  params: {
    location: location
    sku: appConfigurationSku
    name: '${abbrs.appConfigurationStores}${resourceToken}'
    tags: tags
    appInsightsName: ai.outputs.applicationInsightsName
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
    projectConnectionString: projectConnectionString
    agentDeploymentName: agentDeploymentName
    searchConnectionName: searchConnectionName
    aiSearchIndexName: aiSearchIndexName
    searchServiceEndpoint: searchServiceEndpoint
    embeddingDeploymentName: embeddingDeploymentName
    embeddingDeploymentDimensions: embeddingDeploymentDimensions
    agentName: agentName
    agentID: agentID
    projectName: projectName
    appConfigurationEndpoint: configStore.outputs.endpoint
  }
}

module userAcrRolePush 'core/security/role.bicep' = {
  name: 'user-role-acr-push'
  scope: rg
  params: {
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: '8311e382-0749-4cb8-b61a-304f252e45ec'
  }
}

module userAcrRolePull 'core/security/role.bicep' = {
  name: 'user-role-acr-pull'
  scope: rg
  params: {
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: '7f951dda-4ed3-4680-a7ca-43fe172d538d'
  }
}

module userRoleDataScientist 'core/security/role.bicep' = {
  name: 'user-role-data-scientist'
  scope: rg
  params: {
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: 'f6c7c914-8db3-469d-8ca1-694a8f32e121'
  }
}

module userRoleSecretsReader 'core/security/role.bicep' = {
  name: 'user-role-secrets-reader'
  scope: rg
  params: {
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: 'ea01e6af-a1c1-4350-9563-ad00f8c72ec5'
  }
}

module userRoleAzureAIDeveloper 'core/security/role.bicep' = {
  name: 'user-role-azureai-developer'
  scope: rg
  params: {
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: '64702f94-c441-49e6-a78b-ef80e0188fee'
  }
}

module backendRoleSearchIndexDataContributorRG 'core/security/role.bicep' = if (useSearchService) {
  name: 'backend-role-azure-index-data-contributor-rg'
  scope: rg
  params: {
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
  }
}

module backendRoleSearchIndexDataReaderRG 'core/security/role.bicep' = if (useSearchService) {
  name: 'backend-role-azure-index-data-reader-rg'
  scope: rg
  params: {
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
  }
}

module backendRoleSearchServiceContributorRG 'core/security/role.bicep' = if (useSearchService) {
  name: 'backend-role-azure-search-service-contributor-rg'
  scope: rg
  params: {
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
  }
}

module userRoleSearchIndexDataContributorRG 'core/security/role.bicep' = if (useSearchService) {
  name: 'user-role-azure-index-data-contributor-rg'
  scope: rg
  params: {
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
  }
}

module userRoleSearchIndexDataReaderRG 'core/security/role.bicep' = if (useSearchService) {
  name: 'user-role-azure-index-data-reader-rg'
  scope: rg
  params: {
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
  }
}

module userRoleSearchServiceContributorRG 'core/security/role.bicep' = if (useSearchService) {
  name: 'user-role-azure-search-service-contributor-rg'
  scope: rg
  params: {
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
  }
}

module backendRoleAzureAIDeveloperRG 'core/security/role.bicep' = {
  name: 'backend-role-azureai-developer-rg'
  scope: rg
  params: {
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: '64702f94-c441-49e6-a78b-ef80e0188fee'
  }
}

module userRoleConfigStoreDataOwner 'core/security/role.bicep' = {
  name: 'user-role-config-store-data-owner'
  scope: rg
  params: {
    principalId: principalId
    roleDefinitionId: '5ae67dd6-50cb-40e7-96ff-dc2bfa4b606b' 
  }
}

module backendRoleConfigStoreDataOwner 'core/security/role.bicep' = {
  name: 'backend-role-config-store-data-reader'
  scope: rg
  params: {
    principalId: api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: '516239f1-63e1-4d78-a4de-a74fb236a071' 
  }
}

output AZURE_RESOURCE_GROUP string = rg.name

// Outputs required for local development server
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_AIPROJECT_CONNECTION_STRING string = projectConnectionString
output AZURE_AI_AGENT_DEPLOYMENT_NAME string = agentDeploymentName
output AZURE_AI_SEARCH_CONNECTION_NAME string = searchConnectionName
output AZURE_AI_EMBED_DEPLOYMENT_NAME string = embeddingDeploymentName
output AZURE_AI_SEARCH_INDEX_NAME string = aiSearchIndexName
output AZURE_AI_SEARCH_ENDPOINT string = searchServiceEndpoint
output AZURE_AI_EMBED_DIMENSIONS string = embeddingDeploymentDimensions
output AZURE_AI_AGENT_NAME string = agentName
output AZURE_AI_AGENT_ID string = agentID
output APP_CONFIGURATION_ENDPOINT string = configStore.outputs.endpoint

// Outputs required by azd for ACA
output AZURE_CONTAINER_ENVIRONMENT_NAME string = containerApps.outputs.environmentName
output SERVICE_API_IDENTITY_PRINCIPAL_ID string = api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID
output SERVICE_API_NAME string = api.outputs.SERVICE_API_NAME
output SERVICE_API_URI string = api.outputs.SERVICE_API_URI
output SERVICE_API_ENDPOINTS array = ['${api.outputs.SERVICE_API_URI}']
