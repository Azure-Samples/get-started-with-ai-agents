# Azure Function App - Weather Queue Trigger

This directory contains an Azure Function App with a queue trigger that processes weather requests.

**The Function App is always provisioned** when you run `azd up`. Storage is automatically created to support it.

## Function Overview

- **Trigger**: Azure Storage Queue (`weather-input-queue`)
- **Output**: Azure Storage Queue (`weather-output-queue`)
- **Runtime**: Python 3.11

## Local Development

1. Install Azure Functions Core Tools
2. Create `local.settings.json` with your storage connection string
3. Run `func start`

## Deployment

The function app code is automatically deployed when you run `azd up` with `USE_FUNCTION_APP=true`.

```bash
azd env set USE_FUNCTION_APP true
azd up
```

The deployment:
1. Provisions the Function App infrastructure via Bicep
2. Deploys the Python code from this directory
3. Configures managed identity authentication for queue access

## Message Format

### Input Message (weather-input-queue)

```json
{
  "function_args": {
    "location": "Seattle"
  },
  "CorrelationId": "unique-id-123"
}
```

### Output Message (weather-output-queue)

```json
{
  "Value": "Weather is 7 degrees and sunny in Seattle",
  "CorrelationId": "unique-id-123"
}
```
