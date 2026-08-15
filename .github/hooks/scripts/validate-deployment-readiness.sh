#!/bin/bash
# Deployment Readiness Validation Hook
# Validates Azure authentication and project configuration before deployment operations

# Read hook input from stdin
read -r hook_input

# Extract the tool being invoked
tool_name=$(echo "$hook_input" | jq -r '.toolName // empty')

# List of deployment/infrastructure tools to validate for
deployment_tools=("azd" "run_in_terminal" "mcp_azure_mcp_ser_deploy" "mcp_azure_mcp_ser_azd")

# Check if this tool needs validation
needs_validation=false
for tool in "${deployment_tools[@]}"; do
  if [[ "$tool_name" == *"$tool"* ]]; then
    needs_validation=true
    break
  fi
done

# If not a deployment tool, allow immediately
if [ "$needs_validation" = false ]; then
  echo '{"continue": true}'
  exit 0
fi

# Validation checks
checks_passed=true
validation_messages=()

# Check 1: Azure CLI is installed
if ! command -v az &> /dev/null; then
  checks_passed=false
  validation_messages+=("⚠️  Azure CLI not found. Install it first: https://aka.ms/azure-cli")
fi

# Check 2: Azure authentication
if command -v az &> /dev/null; then
  if ! az account show &> /dev/null; then
    checks_passed=false
    validation_messages+=("⚠️  Not authenticated with Azure. Run 'az login' first.")
  fi
fi

# Check 3: azd is available
if ! command -v azd &> /dev/null; then
  checks_passed=false
  validation_messages+=("⚠️  Azure Developer CLI (azd) not found. Install it: https://aka.ms/azd-install")
fi

# Check 4: azure.yaml exists
if [ ! -f "azure.yaml" ]; then
  checks_passed=false
  validation_messages+=("⚠️  azure.yaml not found in workspace root. This project may not be initialized.")
fi

# Check 5: Bicep infrastructure files exist
if [ ! -d "infra" ] || [ -z "$(find infra -name "*.bicep" 2>/dev/null)" ]; then
  checks_passed=false
  validation_messages+=("⚠️  No Bicep files found in infra/ directory. Infrastructure may not be configured.")
fi

# Prepare response
if [ "$checks_passed" = true ]; then
  # All checks passed - allow operation
  echo '{"continue": true}'
  exit 0
else
  # Checks failed - ask for confirmation
  message="Deployment validation found issues:
$(printf '%s\n' "${validation_messages[@]}")

These should be resolved before deployment. Do you want to proceed anyway?"
  
  response=$(jq -n \
    --arg msg "$message" \
    '{
      "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": $msg
      }
    }')
  
  echo "$response"
  exit 0
fi
