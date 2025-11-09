#!/bin/bash

# Quick script to create the federated credential
# Run this in Azure Cloud Shell or your local terminal with Azure CLI

echo "Creating federated credential for GitHub Actions..."

az ad app federated-credential create \
  --id db57485e-6284-434d-ba83-e8fb848cc01d \
  --parameters '{
    "name": "Ksenia-personal-agent-main",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:Skie-Art/Ksenia-personal-agent:ref:refs/heads/main",
    "audiences": ["api://AzureADTokenExchange"],
    "description": "GitHub Actions deployment for main branch"
  }'

echo ""
echo "✅ Federated credential created successfully!"
echo ""
echo "Next steps:"
echo "1. Enable GitHub Actions in your repo"
echo "2. Set up GitHub repository variables"
echo "3. See GITHUB_ACTIONS_SETUP.md for detailed instructions"
