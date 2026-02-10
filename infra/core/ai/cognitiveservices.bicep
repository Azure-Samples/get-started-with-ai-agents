metadata description = 'Creates an Azure Cognitive Services instance.'
param aiServiceName string
param aiProjectName string
param location string = resourceGroup().location
param tags object = {}
@description('The custom subdomain name used to access the API. Defaults to the value of the name parameter.')
param customSubDomainName string = aiServiceName
param disableLocalAuth bool = false
param deployments array = []
param appInsightsId string
param appInsightConnectionString string
param appInsightConnectionName string
param aoaiConnectionName string
param storageAccountId string
param storageAccountConnectionName string
param storageAccountBlobEndpoint string
param sharepointConnectionTarget string = ''
@secure()
param bingConnectionKey string = ''
param bingConnectionTarget string = ''
param bingConnectionResourceId string = ''
@secure()
param bingCustomConnectionKey string = ''
param bingCustomConnectionTarget string = ''
param bingCustomConnectionResourceId string = ''
@secure()
param browserAutomationConnectionKey string = ''
param browserAutomationConnectionTarget string = ''
@secure()
param openApiConnectionKey string = ''
@secure()
param fabricConnectionWorkspaceId string = ''
@secure()
param fabricConnectionArtifactId string = ''
@secure()
param mcpConnectionKey string = ''
param a2aConnectionTarget string = ''

@allowed([ 'Enabled', 'Disabled' ])
param publicNetworkAccess string = 'Enabled'
param sku object = {
  name: 'S0'
}

param allowedIpRules array = []
param networkAcls object = empty(allowedIpRules) ? {
  defaultAction: 'Allow'
} : {
  ipRules: allowedIpRules
  defaultAction: 'Deny'
}

resource account 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
  name: aiServiceName
  location: location
  sku: sku
  kind: 'AIServices'
  identity: {
    type: 'SystemAssigned'
  }
  tags: tags
  properties: {
    allowProjectManagement: true
    customSubDomainName: customSubDomainName
    networkAcls: networkAcls
    publicNetworkAccess: publicNetworkAccess
    disableLocalAuth: disableLocalAuth 
  }
}

resource aiServiceConnection 'Microsoft.CognitiveServices/accounts/connections@2025-04-01-preview' = {
  name: aoaiConnectionName
  parent: account
  properties: {
    category: 'AzureOpenAI'
    authType: 'AAD'
    isSharedToAll: true
    target: account.properties.endpoints['OpenAI Language Model Instance API']
    metadata: {
      ApiType: 'azure'
      ResourceId: account.id
    }
  }
}


// Creates the Azure Foundry connection to your Azure App Insights resource
resource appInsightConnection 'Microsoft.CognitiveServices/accounts/connections@2025-04-01-preview' = {
  name: appInsightConnectionName
  parent: account
  properties: {
    category: 'AppInsights'
    target: appInsightsId
    authType: 'ApiKey'
    isSharedToAll: true
    credentials: {
      key: appInsightConnectionString
    }
    metadata: {
      ApiType: 'Azure'
      ResourceId: appInsightsId
    }
  }
}

// Creates the Azure Foundry connection to your Azure Storage resource
resource storageAccountConnection 'Microsoft.CognitiveServices/accounts/connections@2025-04-01-preview' = {
  name: storageAccountConnectionName
  parent: account
  properties: {
    category: 'AzureStorageAccount'
    target: storageAccountBlobEndpoint
    authType: 'AAD'
    isSharedToAll: true    
    metadata: {
      ApiType: 'Azure'
      ResourceId: storageAccountId
    }
  }
}

module sharepointConnection './connection.bicep' = if (!empty(sharepointConnectionTarget)) {
  name: 'sharepoint-connection'
  dependsOn: [aiProject]
  params: {
    aiServicesAccountName: aiServiceName
    aiProjectName: aiProjectName
    connectionConfig: {
      name: 'sharepoint'
      category: 'CustomKeys'
      target: '_'
      authType: 'CustomKeys'
      isSharedToAll: true
      metadata: {
        type: 'sharepoint_grounding'
      }
      credentials: {
        site_url: sharepointConnectionTarget
      }
    }
  }
}

module bingConnection './connection.bicep' = if (!empty(bingConnectionKey) && !empty(bingConnectionTarget)) {
  name: 'bing-connection'
  dependsOn: [aiProject]
  params: {
    aiServicesAccountName: aiServiceName
    aiProjectName: aiProjectName
    connectionConfig: {
      name: 'bing'
      category: 'GroundingWithBingSearch'
      target: bingConnectionTarget
      authType: 'ApiKey'
      isSharedToAll: false
      metadata: {
        ApiType: 'Azure'
        ResourceId: bingConnectionResourceId
        type: 'bing_grounding'
      }
    }
    apiKey: bingConnectionKey
  }
}

module bingCustomConnection './connection.bicep' = if (!empty(bingCustomConnectionKey) && !empty(bingCustomConnectionTarget)) {
  name: 'bing-custom-connection'
  dependsOn: [aiProject]
  params: {
    aiServicesAccountName: aiServiceName
    aiProjectName: aiProjectName
    connectionConfig: {
      name: 'bing-custom'
      category: 'GroundingWithCustomSearch'
      target: bingCustomConnectionTarget
      authType: 'ApiKey'
      isSharedToAll: false
      metadata: {
        ApiType: 'Azure'
        ResourceId: bingCustomConnectionResourceId
        type: 'bing_custom_search'
      }
    }
    apiKey: bingCustomConnectionKey
  }
}

module browserAutomationConnection './connection.bicep' = if (!empty(browserAutomationConnectionKey) && !empty(browserAutomationConnectionTarget)) {
  name: 'browser-automation-connection'
  dependsOn: [aiProject]
  params: {
    aiServicesAccountName: aiServiceName
    aiProjectName: aiProjectName
    connectionConfig: {
      name: 'browser-automation'
      category: 'Serverless'
      target: browserAutomationConnectionTarget
      authType: 'ApiKey'
      isSharedToAll: false
      metadata: {
        type: 'browser_automation_preview'
      }
    }
    apiKey: browserAutomationConnectionKey
  }
}

module openApiConnection './connection.bicep' = if (!empty(openApiConnectionKey)) {
  name: 'openapi-connection'
  dependsOn: [aiProject]
  params: {
    aiServicesAccountName: aiServiceName
    aiProjectName: aiProjectName
    connectionConfig: {
      name: 'openapi'
      category: 'CustomKeys'
      target: '_'
      authType: 'CustomKeys'
      isSharedToAll: false
      metadata: {
        type: 'openapi'
      }
      credentials: {
        key: openApiConnectionKey
      }      
    }
  }
}

module fabricConnection './connection.bicep' = if (!empty(fabricConnectionWorkspaceId) && !empty(fabricConnectionArtifactId)) {
  name: 'fabric-connection'
  dependsOn: [aiProject]
  params: {
    aiServicesAccountName: aiServiceName
    aiProjectName: aiProjectName
    connectionConfig: {
      name: 'fabric'
      category: 'CustomKeys'
      target: '_'
      authType: 'CustomKeys'
      isSharedToAll: false
      metadata: {
        type: 'fabric_dataagent'
      }
      credentials: {
        'workspace-id': fabricConnectionWorkspaceId
        'artifact-id': fabricConnectionArtifactId
      } 
      sharedUserList: []
    }
  }
}

module mcpConnection './connection.bicep' = if (!empty(mcpConnectionKey)) {
  name: 'mcp-connection'
  dependsOn: [aiProject]
  params: {
    aiServicesAccountName: aiServiceName
    aiProjectName: aiProjectName
    connectionConfig: {
      name: 'mcp'
      category: 'RemoteTool'
      target: 'https://api.githubcopilot.com/mcp'
      authType: 'CustomKeys'
      isSharedToAll: false
      metadata: {
        type: 'custom_MCP'
      }
      credentials: {
        Authorization: 'Bearer github_pat_${mcpConnectionKey}'
      }
    }
  }
}

module a2aConnection './connection.bicep' = if (!empty(a2aConnectionTarget)) {
  name: 'a2a-connection'
  dependsOn: [aiProject]
  params: {
    aiServicesAccountName: aiServiceName
    aiProjectName: aiProjectName
    connectionConfig: {
      name: 'a2a'
      category: 'RemoteA2A'
      target: a2aConnectionTarget
      authType: 'None'
      isSharedToAll: false
      metadata: {
        type: 'custom_A2A'
      }
    }
  }
}

resource aiProject 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  parent: account
  name: aiProjectName
  location: location
  tags: tags  
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    description: aiProjectName
    displayName: aiProjectName
  }
}

@batchSize(1)
resource aiServicesDeployments 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = [for deployment in deployments: {
  parent: account
  name: deployment.name
  properties: {
    model: deployment.model
    raiPolicyName: contains(deployment, 'raiPolicyName') ? deployment.raiPolicyName : null
  }
  sku: contains(deployment, 'sku') ? deployment.sku : {
    name: 'Standard'
    capacity: 20
  }
}]



output endpoint string = account.properties.endpoint
output endpoints object = account.properties.endpoints
output id string = account.id
output name string = account.name
output projectResourceId string = aiProject.id
output projectName string = aiProject.name
output serviceName string = account.name
output projectEndpoint string = aiProject.properties.endpoints['AI Foundry API']
output PrincipalId string = account.identity.principalId
output accountPrincipalId string = account.identity.principalId
output projectPrincipalId string = aiProject.identity.principalId
output storageConnectionId string = storageAccountConnection.id
output storageConnectionName string = storageAccountConnection.name
