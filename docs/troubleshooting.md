# Troubleshooting Guide

This guide provides solutions to common issues you may encounter when deploying and running the AI agents application.

## Provisioning and Deployment Failures

### Resource Provisioning Issues

**Problem**: Timeouts or provisioning resources fail
**Solution**: 
- Change the location of your resource group, as there may be availability constraints for resources
- Call `azd down` and remove your current resources
- Delete the `.azure` folder from your workspace
- Call `azd up` again and select a different region

### Debugging Deployment Issues

**Debug Commands**:
- Use `azd show` to display information about your app and resources
- Use `azd deploy --debug` to enable debugging and logging while deploying the application's code to Azure

**General Checks**:
- Ensure that your `az` and `azd` tools are up to date
- After fully deploying with azd, additional errors in the Azure Portal may indicate that your latest code has not been successfully deployed

## Azure Container Apps

### Container App Boot Issues

**Problem**: ACA does not boot up
**Possible Causes**: Deployment failure due to quota constraints, permission issues, or resource availability
**Solution**: Check failures in the deployment and container app logs in the Azure Portal

### Logging and Debugging

**Console Traces**: 
- Can be found in the Azure Portal, but they may be unreliable
- Use Python's logging with INFO level
- Adjust Azure HTTP logging to WARNING

**Frontend Debugging**:
- Once your ACA is deployed, utilize the browser debugger (F12)
- Clear cache (CTRL+SHIFT+R) to help debug the frontend for better traceability

## Agent Issues

### Agent Responsiveness

**Problem**: Agent is occasionally unresponsive
**Cause**: Your model may have reached its rate limit
**Solution**: 
- Increase quota by adjusting the bicep configuration
- Edit the model in the Microsoft Foundry page for your project's model deployments

### Agent Crashes

**Problem**: Agent is crashing
**Solution**: Confirm that you are using a model that you have deployed to your project

### Session Management

**How it Works**: 
- This application is designed to serve multiple users on multiple browsers
- Uses cookies to ensure that the same thread is reused for conversations across multiple tabs in the same browser
- If the browser is restarted, the old thread will continue to serve the user
- If the application has a new agent after a server restart or a thread is deleted, a new thread will be created without requiring a browser refresh or signaling to the users

**Technical Details**:
- When users submit a message to the web server, the web server will create an agent, thread, and stream back a reply
- The response contains `agent_id` and `thread_id` in cookies
- Each subsequent message sent to the web server will also contain these IDs
- As long as the same agent is being used in the system and the thread can be retrieved in the cookie, the same thread will be used to serve the users

### File Handling Issues

**Best Practices**:
- Use filename-based downloads to avoid storing files in dictionaries
- Intermittent errors may arise when retrieving filenames for file IDs, which may be mitigated by using a single worker and fresh threads for each new agent
- File citation can be enhanced by automatically including filenames to reduce manual steps

## Getting Help

If you continue to experience issues after trying these solutions:

1. Check the [Microsoft Foundry documentation](https://learn.microsoft.com/azure/ai-foundry/)
2. Review the [Azure Container Apps troubleshooting guide](https://learn.microsoft.com/azure/container-apps/troubleshooting)
3. Consult the [Azure Developer CLI reference](https://learn.microsoft.com/azure/developer/azure-developer-cli/reference)
4. For agent-specific issues, refer to the [Azure AI Agents documentation](https://learn.microsoft.com/azure/ai-services/agents/)
