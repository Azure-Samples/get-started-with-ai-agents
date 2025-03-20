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

from azure.ai.projects.aio import AIProjectClient
from fastapi.responses import JSONResponse
from azure.ai.projects.models import (
    Agent,
    MessageDeltaChunk,
    ThreadMessage,
    ThreadRun,
    AsyncAgentEventHandler,
    OpenAIPageableListOfThreadMessage,
    MessageTextContent,
    MessageTextFileCitationAnnotation,
    MessageTextUrlCitationAnnotation,
    RunStep,
    SubmitToolOutputsAction,
    RequiredFunctionToolCall,
    ToolOutput,
    AsyncFunctionTool
)
from user_functions import fns

# Create a logger for this module
logger = logging.getLogger("azureaiapp")

# Set the log level for the azure HTTP logging policy to WARNING (or ERROR)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)

# Define the directory for your templates.
directory = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=directory)

# Create a new FastAPI router
router = fastapi.APIRouter()


def get_ai_client(request: Request) -> AIProjectClient:
    return request.app.state.ai_client


def get_agent(request: Request) -> Agent:
    return request.app.state.agent


def serialize_sse_event(data: Dict) -> str:
    return f"data: {json.dumps(data)}\n\n"

async def get_message_and_annotations(ai_client : AIProjectClient, message: ThreadMessage) -> Dict:
        annotations = []
        # Get file annotations for the file search.
        for annotation in (a.as_dict() for a in message.file_citation_annotations):
            file_id = annotation["file_citation"]["file_id"]
            logger.info(f"Fetching file with ID for annotation {file_id}")
            openai_file = await ai_client.agents.get_file(file_id)
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
    def __init__(self, ai_client: AIProjectClient):
        super().__init__()
        self.ai_client = ai_client
        self.functions = AsyncFunctionTool(fns)

    async def on_message_delta(self, delta: MessageDeltaChunk) -> Optional[str]:
        stream_data = {'content': delta.text, 'type': "message"}
        return serialize_sse_event(stream_data)

    async def on_thread_message(self, message: ThreadMessage) -> Optional[str]:
        try:
            logger.info(f"MyEventHandler: Received thread message, message ID: {message.id}, status: {message.status}")
            if message.status != "completed":
                return None

            logger.info("MyEventHandler: Received completed message")

            stream_data = await get_message_and_annotations(self.ai_client, message)
            stream_data['type'] = "completed_message"
            return serialize_sse_event(stream_data)
        except Exception as e:
            logger.error(f"Error in event handler for thread message: {e}", exc_info=True)
            return None

    async def on_thread_run(self, run: ThreadRun) -> Optional[str]:
        logger.info("MyEventHandler: on_thread_run event received")
        run_information = f"ThreadRun status: {run.status}, thread ID: {run.thread_id}"
        stream_data = {'content': run_information, 'type': 'thread_run'}
        if run.status == "requires_action" and isinstance(run.required_action, SubmitToolOutputsAction):
            tool_calls = run.required_action.submit_tool_outputs.tool_calls

            tool_outputs = []
            for tool_call in tool_calls:
                if isinstance(tool_call, RequiredFunctionToolCall):
                    try:
                        output = await self.functions.execute(tool_call)
                        tool_outputs.append(
                            ToolOutput(
                                tool_call_id=tool_call.id,
                                output=output,
                            )
                        )
                    except Exception as e:
                        print(f"Error executing tool_call {tool_call.id}: {e}")

            print(f"Tool outputs: {tool_outputs}")
            if tool_outputs:
                # Once we receive 'requires_action' status, the next event will be DONE.
                # Here we associate our existing event handler to the next stream.
                await self.ai_client.agents.submit_tool_outputs_to_stream(
                    thread_id=run.thread_id, run_id=run.id, tool_outputs=tool_outputs, event_handler=self
                )

        elif run.status == "failed":
            stream_data['error'] = run.last_error.as_dict()
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
    return templates.TemplateResponse("index.html", {"request": request})


async def get_result(thread_id: str, agent_id: str, ai_client : AIProjectClient) -> AsyncGenerator[str, None]:
    logger.info(f"get_result invoked for thread_id={thread_id} and agent_id={agent_id}")
    try:
        async with await ai_client.agents.create_stream(
            thread_id=thread_id, 
            agent_id=agent_id,
            event_handler=MyEventHandler(ai_client)
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
    ai_client : AIProjectClient = Depends(get_ai_client),
    agent : Agent = Depends(get_agent),
):
    # Retrieve the thread ID from the cookies (if available).
    thread_id = request.cookies.get('thread_id')
    agent_id = request.cookies.get('agent_id')

    # Attempt to get an existing thread. If not found, create a new one.
    try:
        if thread_id and agent_id == agent.id:
            logger.info(f"Retrieving thread with ID {thread_id}")
            thread = await ai_client.agents.get_thread(thread_id)
        else:
            logger.info("Creating a new thread")
            thread = await ai_client.agents.create_thread()
    except Exception as e:
        logger.error(f"Error handling thread: {e}")
        raise HTTPException(status_code=400, detail=f"Error handling thread: {e}")

    thread_id = thread.id
    messages = OpenAIPageableListOfThreadMessage()

    # Create a new message from the user's input.
    try:
        content = []
        response = await ai_client.agents.list_messages(
            thread_id=thread_id,
        )
        for message in response.data:
            formated_message = await get_message_and_annotations(ai_client, message)
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
    ai_client : AIProjectClient = Depends(get_ai_client),
    agent : Agent = Depends(get_agent),
):
    # Retrieve the thread ID from the cookies (if available).
    thread_id = request.cookies.get('thread_id')
    agent_id = request.cookies.get('agent_id')

    # Attempt to get an existing thread. If not found, create a new one.
    try:
        if thread_id and agent_id == agent.id:
            logger.info(f"Retrieving thread with ID {thread_id}")
            thread = await ai_client.agents.get_thread(thread_id)
        else:
            logger.info("Creating a new thread")
            thread = await ai_client.agents.create_thread()
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
        message = await ai_client.agents.create_message(
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
    response = StreamingResponse(get_result(thread_id, agent_id, ai_client), headers=headers)

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
