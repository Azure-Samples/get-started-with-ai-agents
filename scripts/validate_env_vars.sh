#!/bin/bash

# Define environment variables and their regex patterns
declare -A envValidationRules=(
  ["AZURE_EXISTING_AIPROJECT_RESOURCE_ID"]='^/subscriptions/[0-9a-fA-F-]{36}/resourceGroups/[^/]+/providers/Microsoft\.CognitiveServices/accounts/[^/]+/projects/[^/]+$'
)

hasError=0

for envVar in "${!envValidationRules[@]}"; do
  pattern="${envValidationRules[$envVar]}"
  value="${!envVar}"

  if [[ -n "$value" ]]; then
    if ! echo "$value" | grep -Eq "$pattern"; then
      echo "❌ Invalid value for '$envVar'. Expected pattern: $pattern" >&2
      hasError=1
    fi
  fi
done

exit $hasError
