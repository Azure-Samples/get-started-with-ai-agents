# Local Development Guide

This guide helps you set up a local development environment to test and modify the AI agents application. Make sure you first [deployed the app](#deploying-with-azd) to Azure before running the development server.

## Prerequisites

- Python 3.8 or later
- [Node.js](https://nodejs.org/) (v20 or later)
- [pnpm](https://pnpm.io/installation)
- An Azure deployment of the application (completed via `azd up`)

## Environment Setup

### 1. Python Environment

Create a [Python virtual environment](https://docs.python.org/3/tutorial/venv.html#creating-virtual-environments) and activate it:

**On Windows:**
```shell
python -m venv .venv
.venv\scripts\activate
```

**On Linux:**
```shell
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

Navigate to the `src` directory and install Python packages:

```shell
cd src
python -m pip install -r requirements.txt
```

### 3. Frontend Setup

Navigate to the frontend directory and setup for React UI:

```shell
cd src/frontend
pnpm run setup
```

### 4. Environment Configuration

**Important**: The environment variables are stored in the `.azure/<environment-name>/.env` file, **not** in the root or `src` directory. This file is automatically created when running `azd up` and contains all the Azure resource configuration needed for local development.

The application automatically loads environment variables from `.env` in `.azure` folder when running locally.

## Running the Development Server by CLI

### 1. Build Frontend

If you have changes in `src/frontend`, build the React application:

```shell
cd src/frontend
pnpm build
```

The build output will be placed in the `../api/static/react` directory, where the backend can serve it.

### 2. Test Agent Configuration (Optional)

If you have changes in `gunicorn.conf.py`, test the agent configuration:

```shell
cd src
python gunicorn.conf.py    
```

### 3. Start the Server

Run the local development server:

```shell
cd src
python -m uvicorn "api.main:create_app" --factory --reload
```

### 4. Access the Application

Click '<http://127.0.0.1:8000>' in the terminal, which should open a new tab in the browser. Enter your message in the box to test the agent.

## Debugging with VS Code

VS Code provides two debug configurations for easy debugging:

![VS Code Launch Profiles](images/vs_code_launch.png)

### Available Launch Profiles

1. **Debug: Initialize Agent (Gunicorn)** - Runs `gunicorn.conf.py` to test agent initialization and configuration
2. **Debug: FastAPI Server (Uvicorn)** - Runs the FastAPI server with hot-reload for API development

### How to Debug

1. Click on the **Run and Debug** icon in the VS Code left sidebar
2. Select the desired launch profile from the dropdown at the top
3. Click the green **Start Debugging** button
4. Set breakpoints in your code by clicking on the left margin of the editor

### Important: Debugging FastAPI with Existing Agent

When debugging the **FastAPI Server**, you **must** specify the `AZURE_EXISTING_AGENT_ID` environment variable in your `.azure/<environment-name>/.env` file. This tells the application to use an existing agent instead of creating a new one.

Example:
```properties
AZURE_EXISTING_AGENT_ID="agent-template-assistant:1"
```

## Frontend Development and Customization

If you want to modify the frontend application, the key component to understand is `src/frontend/src/components/agents/AgentPreview.tsx`. This component handles:

- **Backend Communication**: Contains the main logic for calling the backend API endpoints
- **Message Handling**: Manages the flow of user messages and agent responses
- **UI State Management**: Controls the display of conversation history and loading states

### Key Areas for Customization

- **Agent Interaction Flow**: Modify how users interact with agents by updating the message handling logic in `AgentPreview.tsx`
- **UI Components**: Customize the chat interface, message bubbles, and response formatting
- **API Integration**: Extend or modify the backend communication patterns established in this component

### Development Workflow

1. Make changes to React components in `src/frontend/src/`
2. Run `pnpm build` to compile the frontend
3. The build output is automatically placed in `../api/static/react` for the backend to serve
4. Restart the local server to see your changes

Start with `AgentPreview.tsx` to understand how the frontend communicates with the backend and how messages are populated in the UI.

## Agent Instructions and Tools Customization

### Creating New Agents

To customize agent instructions or tools when creating **new agents**, modify the agent creation logic in `src/gunicorn.conf.py`:

- **Agent Instructions**: Update the `instructions` variable in the `create_agent()` function (around line 175)
- **Agent Tools**: Modify the `get_available_tool()` function to add or change tools available to the agent
- **Agent Model**: Change the model by updating the `AZURE_AI_AGENT_DEPLOYMENT_NAME` environment variable

### Modifying Existing Agents

**Important**: If you want to modify an **existing agent** that's already deployed, it's recommended to use the **Microsoft Foundry UI** instead of the script:

1. Go to your Microsoft Foundry project
2. Navigate to the Agents section
3. Select your agent
4. Update instructions, tools, or settings directly in the UI

This approach is safer for existing agents as it preserves the agent's conversation history and avoids potential conflicts with running instances.

## File Management and Agent Recreation

### Adding or Updating Files

If you want to add new files to the `src/files/` folder or update the embedded data in `src/data/embeddings.csv` that your agent uses, **you must do this BEFORE agent creation**. The agent creation process in `src/gunicorn.conf.py` uploads and embeds files during initialization.

**Two types of files are processed:**
- **Individual Files**: Files in `src/files/` directory (used for file search)
- **Embedded Data**: Pre-computed embeddings in `src/data/embeddings.csv` (used for Azure AI Search when enabled)

### Important File Update Workflow

1. **Before Agent Creation**: Add or update files in `src/files/` directory and/or update `src/data/embeddings.csv`
2. **Agent Creation**: Run the agent creation process (via local development or deployment)
3. **Files Embedded**: Files are uploaded and embedded into the agent's knowledge base

### If You Need to Update Files After Agent Creation

If you've already created an agent and need to add or update files or embeddings data, you have two options:

#### Option 1: Delete and Recreate Agent (Recommended)
1. Go to your **Microsoft Foundry UI**
2. Navigate to the **Agents** section
3. **Delete the existing agent**
4. Update files in `src/files/` directory and/or `src/data/embeddings.csv`
5. **Restart your local development server** or **run `azd deploy`** again
6. The agent will be recreated with the updated files

#### Option 2: Force Recreation via Deployment
1. Update files in `src/files/` directory and/or `src/data/embeddings.csv`
2. Run `azd deploy` again
3. This will trigger the agent recreation process with updated files

### Why This is Necessary

- The agent creation script only processes files during the initial setup
- File embedding happens once during agent initialization
- Existing agents don't automatically detect file changes
- The agent's vector store/search index needs to be rebuilt with new content

### Agent Behavior After Creation

**Important**: Once an agent has been created and is being used by the application, it operates in a **read-only mode** for file operations:

- **No File Upload**: The agent will NOT upload new files from the `src/files/` directory
- **No Vector Store Creation**: It will NOT create new vector stores for additional files
- **No Reindexing**: It will NOT reindex or re-embed files, even if they've been modified
- **No Embeddings Update**: It will NOT process updates to `src/data/embeddings.csv` for Azure AI Search
- **Uses Existing Resources**: The agent continues to use only the files, vector stores, and search indexes that were created during its initial setup

This means that any changes you make to files in `src/files/` or updates to `src/data/embeddings.csv` after the agent is created will be completely ignored by the running agent. The agent initialization logic in `src/gunicorn.conf.py` only runs during the initial agent creation process, not during normal application operation.

**Best Practice**: Plan your file structure and content before creating agents to minimize the need for recreation.

