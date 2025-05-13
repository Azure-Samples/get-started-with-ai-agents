# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

import asyncio
import json
import os
from typing import AsyncGenerator, Optional, Dict

import fastapi
import logging
from fastapi import Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from opentelemetry import trace
tracer = trace.get_tracer(__name__)

from azure.ai.projects.models import (
   AgentEvaluationRequest,
   AgentEvaluationSamplingConfiguration,
   AgentEvaluationRedactionConfiguration,
   EvaluatorIds
)        

from azure.ai.agents.aio import AgentsClient
from fastapi.responses import JSONResponse
from azure.ai.agents.models import (
    Agent,
    MessageDeltaChunk,
    ThreadMessage,
    ThreadRun,
    AsyncAgentEventHandler,
    RunStep
)

# Create a logger for this module
logger = logging.getLogger("azureaiapp")

# Set the log level for the azure HTTP logging policy to WARNING (or ERROR)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)

# Define the directory for your templates.
directory = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=directory)

# Create a new FastAPI router
router = fastapi.APIRouter()


def get_agent_client(request: Request) -> AgentsClient:
    return request.app.state.agent_client


def get_agent(request: Request) -> Agent:
    return request.app.state.agent

def run_agent_evaluation(request: Request, thread_id, run_id):
    app_insights_connection_string = request.app.state.application_insights_connection_string
    agent_evaluation_request = AgentEvaluationRequest(
        run_id=run_id,
        thread_id=thread_id,
        evaluators={
            "Relevance": {"Id": EvaluatorIds.RELEVANCE.value},
            #"ResponseCompleteness": {"Id": EvaluatorIds.RESPONSE_COMPLETENESS.value},
            "TaskAdherence": {"Id": EvaluatorIds.TASK_ADHERENCE.value},
            "ToolCallAccuracy": {"Id": EvaluatorIds.TOOL_CALL_ACCURACY.value},
        },
        sampling_configuration=AgentEvaluationSamplingConfiguration(
            name="default",
            sampling_percent=100,
        ),
        redaction_configuration=AgentEvaluationRedactionConfiguration(
            redact_score_properties=False,
        ),
        app_insights_connection_string=app_insights_connection_string,
    )
    
    async def run_evaluation():
        try:        
            project = request.app.state.project
            logger.info(f"Running agent evaluation on thread ID {thread_id} and run ID {run_id}")
            agent_evaluation_response = await project.evaluations.create_agent_evaluation(
                evaluation=agent_evaluation_request
            )
            logger.info(f"Evaluation response: {agent_evaluation_response}")
        except Exception as e:
            logger.error(f"Error creating agent evaluation: {e}")

    # Create a new task to run the evaluation asynchronously
    asyncio.create_task(run_evaluation())

    
def get_react_bundle_path() -> str:
    """Get the path to the latest React bundle from the Vite manifest file."""
    manifest_path = os.path.join(os.path.dirname(__file__), "static", "react", ".vite", "manifest.json")
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            # Get the main entry point bundle
            if "src/main.jsx" in manifest:
                return f"/static/react/{manifest['src/main.jsx']['file']}"
            # Fallback to any entry point if the expected one isn't found
            for key, value in manifest.items():
                if value.get("isEntry", False):
                    return f"/static/react/{value['file']}"
            # If no entries are found, return a default path
            logger.warning("No entries found in Vite manifest, using fallback path")
            return "/static/react/assets/main.js"
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        logger.error(f"Error reading Vite manifest: {e}")
        # Return a default path if the manifest can't be read
        return "/static/react/assets/main.js"


def serialize_sse_event(data: Dict) -> str:
    return f"data: {json.dumps(data)}\n\n"

async def get_message_and_annotations(agent_client : AgentsClient, message: ThreadMessage) -> Dict:
        annotations = []
        # Get file annotations for the file search.
        for annotation in (a.as_dict() for a in message.file_citation_annotations):
            file_id = annotation["file_citation"]["file_id"]
            logger.info(f"Fetching file with ID for annotation {file_id}")
            openai_file = await agent_client.files.get(file_id)
            annotation["file_name"] = openai_file.filename
            logger.info(f"File name for annotation: {annotation['file_name']}")
            annotations.append(annotation)

        # Get url annotation for the index search.
        for url_annotation in message.url_citation_annotations:
            annotation = url_annotation.as_dict()
            annotation["file_name"] = annotation['url_citation']['title']
            logger.info(f"File name for annotation: {annotation['file_name']}")
            annotations.append(annotation)
                
        return {
                'content': message.text_messages[0].text.value,
                'annotations': annotations
            }
class MyEventHandler(AsyncAgentEventHandler[str]):
    def __init__(self, request : Request, agent_client: Agent):
        super().__init__()
        self.agent_client = agent_client
        self.request = request

    async def on_message_delta(self, delta: MessageDeltaChunk) -> Optional[str]:
        stream_data = {'content': delta.text, 'type': "message"}
        return serialize_sse_event(stream_data)

    async def on_thread_message(self, message: ThreadMessage) -> Optional[str]:
        try:
            logger.info(f"MyEventHandler: Received thread message, message ID: {message.id}, status: {message.status}")
            if message.status != "completed":
                return None

            logger.info("MyEventHandler: Received completed message")

            stream_data = await get_message_and_annotations(self.agent_client, message)
            stream_data['type'] = "completed_message"
            return serialize_sse_event(stream_data)
        except Exception as e:
            logger.error(f"Error in event handler for thread message: {e}", exc_info=True)
            return None

    async def on_thread_run(self, run: ThreadRun) -> Optional[str]:
        logger.info("MyEventHandler: on_thread_run event received")
        run_information = f"ThreadRun status: {run.status}, thread ID: {run.thread_id}"
        stream_data = {'content': run_information, 'type': 'thread_run'}
        if run.status == "failed":
            stream_data['error'] = run.last_error.as_dict()
        
        # automatically run agent evaluation when the run is completed
        if run.status == "completed":
            run_agent_evaluation(self.request, run.thread_id, run.id)
        return serialize_sse_event(stream_data)

    async def on_error(self, data: str) -> Optional[str]:
        logger.error(f"MyEventHandler: on_error event received: {data}")
        stream_data = {'type': "stream_end"}
        return serialize_sse_event(stream_data)

    async def on_done(self) -> Optional[str]:
        logger.info("MyEventHandler: on_done event received")
        stream_data = {'type': "stream_end"}
        return serialize_sse_event(stream_data)

    async def on_run_step(self, step: RunStep) -> Optional[str]:
        logger.info(f"Step {step['id']} status: {step['status']}")
        step_details = step.get("step_details", {})
        tool_calls = step_details.get("tool_calls", [])

        if tool_calls:
            logger.info("Tool calls:")
            for call in tool_calls:
                azure_ai_search_details = call.get("azure_ai_search", {})
                if azure_ai_search_details:
                    logger.info(f"azure_ai_search input: {azure_ai_search_details.get('input')}")
                    logger.info(f"azure_ai_search output: {azure_ai_search_details.get('output')}")
        return None

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # Check if the useReactApp query parameter is present and set to 'true'
    use_react_app = request.query_params.get('useReactApp', '').lower() == 'true'
    
    # Use different template files based on whether React is enabled
    template_name = "index_react.html" if use_react_app else "index.html"
    
    return templates.TemplateResponse(
        template_name, 
        {
            "request": request,
        }
    )


async def get_result(request : Request, thread_id: str, agent_id: str, agent_client : AgentsClient) -> AsyncGenerator[str, None]:
    logger.info(f"get_result invoked for thread_id={thread_id} and agent_id={agent_id}")
    try:
        async with await agent_client.runs.stream(
            thread_id=thread_id, 
            agent_id=agent_id,
            event_handler=MyEventHandler(request, agent_client)
        ) as stream:
            logger.info("Successfully created stream; starting to process events")
            async for event in stream:
                _, _, event_func_return_val = event
                logger.debug(f"Received event: {event}")
                if event_func_return_val:
                    logger.info(f"Yielding event: {event_func_return_val}")
                    yield event_func_return_val
                else:
                    logger.debug("Event received but no data to yield")
    except Exception as e:
        logger.exception(f"Exception in get_result: {e}")
        yield serialize_sse_event({'type': "error", 'message': str(e)})


@router.get("/chat/history")
async def history(
    request: Request,
    agent_client : AgentsClient = Depends(get_agent_client),
    agent : Agent = Depends(get_agent),
):
    # Retrieve the thread ID from the cookies (if available).
    thread_id = request.cookies.get('thread_id')
    agent_id = request.cookies.get('agent_id')

    # Attempt to get an existing thread. If not found, create a new one.
    try:
        if thread_id and agent_id == agent.id:
            logger.info(f"Retrieving thread with ID {thread_id}")
            thread = await agent_client.threads.get(thread_id)
        else:
            logger.info("Creating a new thread")
            thread = await agent_client.threads.create()
    except Exception as e:
        logger.error(f"Error handling thread: {e}")
        raise HTTPException(status_code=400, detail=f"Error handling thread: {e}")

    thread_id = thread.id
    agent_id = agent.id

    # Create a new message from the user's input.
    try:
        content = []
        response = agent_client.messages.list(
            thread_id=thread_id,
        )
        async for message in response:
            formated_message = await get_message_and_annotations(agent_client, message)
            formated_message['role'] = message.role
            content.append(formated_message)
                
                                        
        logger.info(f"List message, thread ID: {thread_id}")
        response = JSONResponse(content=content)
    
        # Update cookies to persist the thread and agent IDs.
        response.set_cookie("thread_id", thread_id)
        response.set_cookie("agent_id", agent_id)
        return response
    except Exception as e:
        logger.error(f"Error listing message: {e}")
        raise HTTPException(status_code=500, detail=f"Error list message: {e}")


@router.post("/chat")
async def chat(
    request: Request,
    agent_client : AgentsClient = Depends(get_agent_client),
    agent : Agent = Depends(get_agent),
):
    with tracer.start_as_current_span("chat_request"):
        # Retrieve the thread ID from the cookies (if available).
        thread_id = request.cookies.get('thread_id')
        agent_id = request.cookies.get('agent_id')

        # Attempt to get an existing thread. If not found, create a new one.
        try:
            if thread_id and agent_id == agent.id:
                logger.info(f"Retrieving thread with ID {thread_id}")
                thread = await agent_client.threads.get(thread_id)
            else:
                logger.info("Creating a new thread")
                thread = await agent_client.threads.create()
        except Exception as e:
            logger.error(f"Error handling thread: {e}")
            raise HTTPException(status_code=400, detail=f"Error handling thread: {e}")

        thread_id = thread.id
        agent_id = agent.id

        # Parse the JSON from the request.
        try:
            user_message = await request.json()
        except Exception as e:
            logger.error(f"Invalid JSON in request: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid JSON in request: {e}")

        logger.info(f"user_message: {user_message}")

        # Create a new message from the user's input.
        try:
            message = await agent_client.messages.create(
                thread_id=thread_id,
                role="user",
                content=user_message.get('message', '')
            )
            logger.info(f"Created message, message ID: {message.id}")
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            raise HTTPException(status_code=500, detail=f"Error creating message: {e}")

        # Set the Server-Sent Events (SSE) response headers.
        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
        logger.info(f"Starting streaming response for thread ID {thread_id}")

        # Create the streaming response using the generator.
        response = StreamingResponse(get_result(request, thread_id, agent_id, agent_client), headers=headers)

        # Update cookies to persist the thread and agent IDs.
        response.set_cookie("thread_id", thread_id)
        response.set_cookie("agent_id", agent_id)
        return response


@router.get("/fetch-document")
async def fetch_document(request: Request):
    file_name = request.query_params.get('file_name')
    if not file_name:
        raise HTTPException(status_code=400, detail="file_name is required")

    folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'files'))

    file_path = os.path.join(folder_path, file_name)

    if file_name not in os.listdir(folder_path): 
        raise HTTPException(status_code=404, detail="File not found")

    try:
        data = await asyncio.to_thread(read_file, file_path)
        return PlainTextResponse(data)
    except Exception as e:
        logger.error(f"Error fetching document for file_name {file_name}: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


def read_file(path: str) -> str:
    with open(path, 'r') as file:
        return file.read()
