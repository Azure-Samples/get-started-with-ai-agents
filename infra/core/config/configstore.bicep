metadata description = 'Creates an Azure App Configuration store.'

@description('The name for the Azure App Configuration store')
param name string

@description('The Azure region/location for the Azure App Configuration store')
param location string = resourceGroup().location

@description('The SKU for the Azure App Configuration store')
param sku string

@description('Custom tags to apply to the Azure App Configuration store')
param tags object = {}

@description('Specifies the names of the key-value resources. The name is a combination of key and label with $ as delimiter. The label is optional.')
param keyValueNames array = []

@description('Specifies the values of the key-value resources.')
param keyValueValues array = []

@description('The Application Insights ID linked to the Azure App Configuration store')
param appInsightsName string

resource configStore 'Microsoft.AppConfiguration/configurationStores@2023-09-01-preview' = {
  name: name
  location: location
  sku: {
    name: sku
  }
  tags: tags
  properties: {
    encryption: {}
    disableLocalAuth: true
    enablePurgeProtection: false
    experimentation:{}
    dataPlaneProxy:{
      authenticationMode: 'Pass-through'
      privateLinkDelegation: 'Disabled'
    }
    telemetry: {
      resourceId: appInsights.id
    }
  }
}

resource configStoreKeyValue 'Microsoft.AppConfiguration/configurationStores/keyValues@2023-03-01' = [for (item, i) in keyValueNames: {
  parent: configStore
  name: item
  properties: {
    value: keyValueValues[i]
    tags: tags
  }
}]

resource appInsights  'Microsoft.Insights/components@2020-02-02-preview'  existing = {
  name: appInsightsName
}

output endpoint string = configStore.properties.endpoint
output name string = configStore.name
