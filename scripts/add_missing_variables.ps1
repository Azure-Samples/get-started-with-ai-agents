# PowerShell script to add missing GitHub Actions variables

$REPO = "Skie-Art/Ksenia-personal-agent"

Write-Host "Adding missing variables..." -ForegroundColor Cyan

# Application Insights (you DO have this!)
gh variable set AZURE_APPLICATION_INSIGHTS_NAME -b "appi-fpfde4hlibpgs" -R $REPO
gh variable set USE_APPLICATION_INSIGHTS -b "true" -R $REPO

# These might exist - check your resource group, otherwise workflow will create them
gh variable set AZURE_KEYVAULT_NAME -b "kv-fpfde4hlibpgs" -R $REPO
gh variable set AZURE_LOG_ANALYTICS_WORKSPACE_NAME -b "log-fpfde4hlibpgs" -R $REPO

# Search Service - leave empty since you're not using it
gh variable set AZURE_SEARCH_SERVICE_NAME -b "" -R $REPO

Write-Host "[OK] Missing variables added!" -ForegroundColor Green
Write-Host ""
Write-Host "Updated:" -ForegroundColor Yellow
Write-Host "  - AZURE_APPLICATION_INSIGHTS_NAME = appi-fpfde4hlibpgs" -ForegroundColor Green
Write-Host "  - USE_APPLICATION_INSIGHTS = true" -ForegroundColor Green
Write-Host "  - AZURE_KEYVAULT_NAME = kv-fpfde4hlibpgs" -ForegroundColor White
Write-Host "  - AZURE_LOG_ANALYTICS_WORKSPACE_NAME = log-fpfde4hlibpgs" -ForegroundColor White
Write-Host "  - AZURE_SEARCH_SERVICE_NAME = (empty)" -ForegroundColor White
Write-Host ""
Write-Host "Try running the deployment again!" -ForegroundColor Cyan
