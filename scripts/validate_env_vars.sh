#!/bin/bash

# Define environment variable names and their regex patterns
envVars=("AZURE_EXISTING_AIPROJECT_RESOURCE_ID")
patterns=('^/subscriptions/[0-9a-fA-F-]{36}/resourceGroups/[^/]+/providers/Microsoft\.CognitiveServices/accounts/[^/]+/projects/[^/]+$')

hasError=0

for i in "${!envVars[@]}"; do
  envVar="${envVars[$i]}"
  pattern="${patterns[$i]}"
  value="${!envVar}"

  if [[ -n "$value" ]]; then
    if [[ ! "$value" =~ $pattern ]]; then
      echo "❌ Invalid value for '$envVar'. Expected pattern: $pattern" >&2
      hasError=1
    fi
  fi
done

exit $hasError
