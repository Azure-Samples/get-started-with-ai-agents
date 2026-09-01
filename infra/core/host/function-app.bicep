metadata description = 'Creates an Azure Function App for queue-triggered functions.'

param name string
param location string = resourceGroup().location
param tags object = {}

@description('The name of the App Service Plan')
param appServicePlanName string

@description('App Service Plan SKU')
param appServicePlanSku string = 'EP1'

@description('Storage Account name')
param storageAccountName string

@description('Application Insights connection string')
param applicationInsightsConnectionString string = ''

@description('User-assigned managed identity resource ID')
param identityId string

@description('The runtime stack for the Function App')
param runtime string = 'python'

@description('The runtime version')
param runtimeVersion string = '3.11'

resource functionIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: last(split(identityId, '/'))
}

resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanName
  location: location
  tags: tags
  sku: {
    name: appServicePlanSku
    tier: 'ElasticPremium'
  }
  properties: {
    reserved: true // Required for Linux
    maximumElasticWorkerCount: 3
  }
  kind: 'linux'
}

resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: name
  location: location
  tags: union(tags, { 'azd-service-name': 'function_app' })
  kind: 'functionapp,linux'
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identityId}': {}
    }
  }
  properties: {
    serverFarmId: appServicePlan.id
    reserved: true
    siteConfig: {
      linuxFxVersion: '${runtime}|${runtimeVersion}'
      appSettings: [
        {
          name: 'AzureWebJobsStorage__accountName'
          value: storageAccountName
        }
        {
          name: 'AzureWebJobsStorage__credential'
          value: 'managedidentity'
        }
        {
          name: 'AzureWebJobsStorage__clientId'
          value: functionIdentity.properties.clientId
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: runtime
        }
        {
          name: 'STORAGE_CONNECTION__queueServiceUri'
          value: 'https://${storageAccountName}.queue.${environment().suffixes.storage}'
        }
        {
          name: 'STORAGE_CONNECTION__credential'
          value: 'managedidentity'
        }
        {
          name: 'STORAGE_CONNECTION__clientId'
          value: functionIdentity.properties.clientId
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: applicationInsightsConnectionString
        }
      ]
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
    }
    httpsOnly: true
  }
}

output id string = functionApp.id
output name string = functionApp.name
output principalId string = functionIdentity.properties.principalId
output identityId string = functionIdentity.id
output defaultHostname string = functionApp.properties.defaultHostName
