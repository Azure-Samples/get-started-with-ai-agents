@minLength(1)
@description('Primary location for all resources')
param location string

@description('The AI Project resource name.')
param aiProjectName string
@description('The Storage Account resource name.')
param storageAccountName string
@description('The AI Services resource name.')
param aiServicesName string
@description('The AI Services model deployments.')
param aiServiceModelDeployments array = []
@description('The Log Analytics resource name.')
param logAnalyticsName string = ''
@description('The Application Insights resource name.')
param applicationInsightsName string = ''
@description('The Azure Search resource name.')
param searchServiceName string = ''
@description('The Application Insights connection name.')
param appInsightConnectionName string
param tags object = {}
param aoaiConnectionName string
module storageAccount '../storage/storage-account.bicep' = {
  name: 'storageAccount'
  params: {
    location: location
    tags: tags
    name: storageAccountName
    containers: [
      {
        name: 'default'
      }
    ]
    files: [
      {
        name: 'default'
      }
    ]
    queues: [
      {
        name: 'default'
      }
    ]
    tables: [
      {
        name: 'default'
      }
    ]
    deleteRetentionPolicy: {
      allowPermanentDelete: false
      enabled: false
    }
    shareDeleteRetentionPolicy: {
      enabled: true
      days: 7
    }
  }
}

module logAnalytics '../monitor/loganalytics.bicep' =
  if (!empty(logAnalyticsName)) {
    name: 'logAnalytics'
    params: {
      location: location
      tags: tags
      name: logAnalyticsName
    }
  }

module applicationInsights '../monitor/applicationinsights.bicep' =
  if (!empty(applicationInsightsName) && !empty(logAnalyticsName)) {
    name: 'applicationInsights'
    params: {
      location: location
      tags: tags
      name: applicationInsightsName
      logAnalyticsWorkspaceId: !empty(logAnalyticsName) ? logAnalytics.outputs.id : ''
    }
  }


module cognitiveServices '../ai/cognitiveservices.bicep' = {
  name: 'cognitiveServices'
  params: {
    location: location
    tags: tags
    aiServiceName: aiServicesName
    aiProjectName: aiProjectName
    deployments: aiServiceModelDeployments
    appInsightsId: applicationInsights.outputs.id
    appInsightConnectionName: appInsightConnectionName
    appInsightConnectionString: applicationInsights.outputs.connectionString
    storageAccountId: storageAccount.outputs.id
    storageAccountConnectionName: 'storageAccount'
    storageAccountBlobEndpoint: storageAccount.outputs.primaryEndpoints.blob
    aoaiConnectionName: aoaiConnectionName
  }
}

module accountStorageRoleAssignment  '../../core/security/role.bicep' = {
  name: 'ai-account-role-storage-contributor'
  params: {
    principalType: 'ServicePrincipal'
    principalId: cognitiveServices.outputs.accountPrincipalId
    roleDefinitionId: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe' // Storage Blob Data Contributor
  }
}

module projectStorageRoleAssignment  '../../core/security/role.bicep' = {
  name: 'ai-project-role-storage-contributor'
  params: {
    principalType: 'ServicePrincipal'
    principalId: cognitiveServices.outputs.projectPrincipalId
    roleDefinitionId: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe' // Storage Blob Data Contributor
  }
}

module projectAIUserRoleAssignment  '../../core/security/role.bicep' = {
  name: 'ai-project-role-ai-user'
  params: {
    principalType: 'ServicePrincipal'
    principalId: cognitiveServices.outputs.projectPrincipalId
    roleDefinitionId: '53ca6127-db72-4b80-b1b0-d745d6d5456d' // Azure AI User
  }
}


module searchService '../search/search-services.bicep' =
  if (!empty(searchServiceName)) {
    dependsOn: [cognitiveServices]
    name: 'searchService'
    params: {
      location: location
      tags: tags
      name: searchServiceName
      semanticSearch: 'free'
      authOptions: { aadOrApiKey: { aadAuthFailureMode: 'http401WithBearerChallenge'}}
      projectName: cognitiveServices.outputs.projectName
      serviceName: cognitiveServices.outputs.serviceName
    }
  }

module searchServiceStorageRoleAssignment '../../core/security/role.bicep' =
  if (!empty(searchServiceName)) {
    name: 'search-service-role-storage-blob-data-reader'
    params: {
      principalType: 'ServicePrincipal'
      principalId: !empty(searchServiceName) ? searchService.outputs.principalId : ''
      roleDefinitionId: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1' // Storage Blob Data Reader
    }
  }


// Outputs
output storageAccountId string = storageAccount.outputs.id
output storageAccountName string = storageAccount.outputs.name
output storageConnectionId string = cognitiveServices.outputs.storageConnectionId
output storageConnectionName string = cognitiveServices.outputs.storageConnectionName

output applicationInsightsId string = !empty(applicationInsightsName) ? applicationInsights.outputs.id : ''
output applicationInsightsName string = !empty(applicationInsightsName) ? applicationInsights.outputs.name : ''
output logAnalyticsWorkspaceId string = !empty(logAnalyticsName) ? logAnalytics.outputs.id : ''
output logAnalyticsWorkspaceName string = !empty(logAnalyticsName) ? logAnalytics.outputs.name : ''

output aiServiceId string = cognitiveServices.outputs.id
output aiServicesName string = cognitiveServices.outputs.name
output aiProjectEndpoint string = cognitiveServices.outputs.projectEndpoint
output aiServicePrincipalId string = cognitiveServices.outputs.accountPrincipalId

output searchServiceId string = !empty(searchServiceName) ? searchService.outputs.id : ''
output searchServiceName string = !empty(searchServiceName) ? searchService.outputs.name : ''
output searchServiceEndpoint string = !empty(searchServiceName) ? searchService.outputs.endpoint : ''

output projectResourceId string = cognitiveServices.outputs.projectResourceId
output searchConnectionId string = !empty(searchServiceName) ? searchService.outputs.searchConnectionId : ''
