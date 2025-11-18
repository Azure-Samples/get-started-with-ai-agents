metadata description = 'Assigns MonitoringMetricsContributor role to Application Insights.'
param appInsightsName string
param principalId string
@allowed([
  'Device'
  'ForeignGroup'
  'Group'
  'ServicePrincipal'
  'User'
  ''
])
param principalType string = ''

resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

//var monitoringMetricsPublisherRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '3913510d-42f4-4e42-8a64-420c390055eb')
var monitoringMetricsContributorRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '749f88d5-cbae-40b8-bcfc-e573ddc772fa')

resource monitoringMetricsContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: appInsights // Use when specifying a scope that is different than the deployment scope
  name: guid(subscription().id, resourceGroup().id, principalId, monitoringMetricsContributorRole)
  properties: {
    principalType: principalType
    roleDefinitionId: monitoringMetricsContributorRole
    principalId: principalId
  }
  dependsOn: [
    resourceGroup() // Explicitly declare dependency on the resource group
]
}
