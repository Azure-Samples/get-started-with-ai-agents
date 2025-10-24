# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional, Dict


import fastapi
from fastapi import Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

import logging
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from azure.ai.projects.models import AgentVersionObject, AgentReference
from openai.types.conversations.message import Message
from openai.types.responses import Response, ResponseOutputText, ResponseOutputMessage, ResponseInputText, ResponseInputMessageItem
from openai.types.conversations import Conversation
from openai.types.responses.response_output_text import AnnotationFileCitation

# from azure.ai.agents.aio import AgentsClient
# from azure.ai.agents.models import (
#     Agent,
#     MessageDeltaChunk,
#     ThreadMessage,
#     ThreadRun,
#     AsyncAgentEventHandler,
#     RunStep
# )
# from azure.ai.projects.models import (
#    AgentEvaluationRequest,
#    AgentEvaluationSamplingConfiguration,
#    AgentEvaluationRedactionConfiguration,
#    EvaluatorIds
# )
from azure.ai.projects.aio import AIProjectClient

import httpx
from openai.types.responses import ResponseTextDeltaEvent, ResponseCompletedEvent, ResponseTextDoneEvent, ResponseCreatedEvent, ResponseOutputItemDoneEvent

from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncOpenAI
from openai.resources.responses import Responses
from sample_helpers import AsyncOpenAILoggingTransport

created_at: Dict[str, str] = {}

# Create a logger for this module
logger = logging.getLogger("azureaiapp")

# Set the log level for the azure HTTP logging policy to WARNING (or ERROR)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)

from opentelemetry import trace
tracer = trace.get_tracer(__name__)

# Define the directory for your templates.
directory = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=directory)

# Create a new FastAPI router
router = fastapi.APIRouter()

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Optional
import secrets

security = HTTPBasic()

username = os.getenv("WEB_APP_USERNAME")
password = os.getenv("WEB_APP_PASSWORD")
basic_auth = username and password

def authenticate(credentials: Optional[HTTPBasicCredentials] = Depends(security)) -> None:

    if not basic_auth:
        logger.info("Skipping authentication: WEB_APP_USERNAME or WEB_APP_PASSWORD not set.")
        return
    
    correct_username = secrets.compare_digest(credentials.username, username)
    correct_password = secrets.compare_digest(credentials.password, password)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return

auth_dependency = Depends(authenticate) if basic_auth else None


def get_ai_project(request: Request) -> AIProjectClient:
    return request.app.state.ai_project

def get_agent_version_obj(request: Request) -> AgentVersionObject:
    return request.app.state.agent_version_obj

async def get_openai_client(request: Request) -> AsyncOpenAI:
    return await get_ai_project(request).get_openai_client()

def get_app_insights_conn_str(request: Request) -> str:
    if hasattr(request.app.state, "application_insights_connection_string"):
        return request.app.state.application_insights_connection_string
    else:
        return None

def serialize_sse_event(data: Dict) -> str:
    return f"data: {json.dumps(data)}\n\n"

async def get_or_create_conversation(
    openai_client: AsyncOpenAI,
    conversation_id: Optional[str],
    agent_id: Optional[str],
    current_agent_id: str
) -> Conversation:
    """
    Get an existing conversation or create a new one.
    Returns the conversation_id.
    """
    conversation: Optional[Conversation] = None
    
    # Attempt to get an existing conversation if we have matching agent and conversation IDs
    if conversation_id and agent_id == current_agent_id:
        try:
            logger.info(f"Using existing conversation with ID {conversation_id}")
            conversation = await openai_client.conversations.retrieve(conversation_id=conversation_id)
            logger.info(f"Retrieved conversation: {conversation.id}")
        except Exception as e:
            logger.error(f"Error retrieving conversation: {e}")

    # Create a new conversation if we don't have one
    if not conversation:
        try:
            logger.info("Creating a new conversation")
            conversation = await openai_client.conversations.create()
            logger.info(f"Generated new conversation ID: {conversation.id}")
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            raise HTTPException(status_code=400, detail=f"Error handling conversation: {e}")
    
    return conversation

async def get_message_and_annotations(event: Message | ResponseOutputMessage) -> Dict:
    annotations = []
    # Get file annotations for the file search.
    text = ""
    content = event.content[0]
    if isinstance(content, ResponseOutputText) or isinstance(content, ResponseInputText):
        text = content.text
    if isinstance(content, ResponseOutputText):
        for annotation in content.annotations:
            if isinstance(annotation, AnnotationFileCitation):
                ann = {
                    'file_name': annotation.filename,
                    "index": annotation.index
                }
                annotations.append(ann)

    # Get url annotation for the index search.
    # for url_annotation in event.url_citation_annotations:
    #     annotation = url_annotation.as_dict()
    #     annotation["file_name"] = annotation['url_citation']['title']
    #     logger.info(f"File name for annotation: {annotation['file_name']}")
    #     annotations.append(annotation)
            
    return {
        'content': text,
        'annotations': annotations
    }

# class MyEventHandler(AsyncAgentEventHandler[str]):
#     def __init__(self, ai_project: AIProjectClient, app_insights_conn_str: str):
#         super().__init__()
#         self.agent_client = ai_project.agents
#         self.ai_project = ai_project
#         self.app_insights_conn_str = app_insights_conn_str

#     async def on_message_delta(self, delta: MessageDeltaChunk) -> Optional[str]:
#         stream_data = {'content': delta.text, 'type': "message"}
#         return serialize_sse_event(stream_data)

#     async def on_thread_message(self, message: ThreadMessage) -> Optional[str]:
#         try:
#             logger.info(f"MyEventHandler: Received thread message, message ID: {message.id}, status: {message.status}")
#             if message.status != "completed":
#                 return None

#             logger.info("MyEventHandler: Received completed message")

#             stream_data = await get_message_and_annotations(self.agent_client, message)
#             stream_data['type'] = "completed_message"
#             return serialize_sse_event(stream_data)
#         except Exception as e:
#             logger.error(f"Error in event handler for thread message: {e}", exc_info=True)
#             return None

#     async def on_thread_run(self, run: ThreadRun) -> Optional[str]:
#         logger.info("MyEventHandler: on_thread_run event received")
#         run_information = f"ThreadRun status: {run.status}, thread ID: {run.thread_id}"
#         stream_data = {'content': run_information, 'type': 'thread_run'}
#         if run.status == "failed":
#             stream_data['error'] = run.last_error.as_dict()
#         # automatically run agent evaluation when the run is completed
#         if run.status == "completed":
#             run_agent_evaluation(run.thread_id, run.id, self.ai_project, self.app_insights_conn_str)
#         return serialize_sse_event(stream_data)

#     async def on_error(self, data: str) -> Optional[str]:
#         logger.error(f"MyEventHandler: on_error event received: {data}")
#         stream_data = {'type': "stream_end"}
#         return serialize_sse_event(stream_data)

#     async def on_done(self) -> Optional[str]:
#         logger.info("MyEventHandler: on_done event received")
#         stream_data = {'type': "stream_end"}
#         return serialize_sse_event(stream_data)

#     async def on_run_step(self, step: RunStep) -> Optional[str]:
#         logger.info(f"Step {step['id']} status: {step['status']}")
#         step_details = step.get("step_details", {})
#         tool_calls = step_details.get("tool_calls", [])

#         if tool_calls:
#             logger.info("Tool calls:")
#             for call in tool_calls:
#                 azure_ai_search_details = call.get("azure_ai_search", {})
#                 if azure_ai_search_details:
#                     logger.info(f"azure_ai_search input: {azure_ai_search_details.get('input')}")
#                     logger.info(f"azure_ai_search output: {azure_ai_search_details.get('output')}")
#         return None

@router.get("/", response_class=HTMLResponse)
async def index(request: Request, _ = auth_dependency):
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
        }
    )

async def save_created_at(openai_client: AsyncOpenAI, response: Response,  input_created_at: int, output_message_id):
    # Note: OpenAI doesn't support retrieving created_at by message ID, so we save it by local dictionary
    # TODO:  Need to retest
    max_retries = 5
    retry_delay = 3  # seconds
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Saving created_at for response {response.id} (attempt {attempt + 1}/{max_retries})")
            input_items = await openai_client.responses.input_items.list(response_id=response.id, order="desc")
            async for input_item in input_items:
                if isinstance(input_item, ResponseInputMessageItem):
                    created_at[input_item.id] = datetime.fromtimestamp(input_created_at, timezone.utc).astimezone().strftime("%m/%d/%y, %I:%M %p")
                    created_at[output_message_id] = datetime.fromtimestamp(response.created_at, timezone.utc).astimezone().strftime("%m/%d/%y, %I:%M %p")
                    return
            
            logger.info(f"Successfully saved created_at for response {response.id}")
            return  # Success, exit the retry loop
            
        except Exception as e:
            logger.error(f"Error updating message created_at (attempt {attempt + 1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:  # Don't wait after the last attempt
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"Failed to save created_at after {max_retries} attempts")


async def get_result(
    agent_name: str,
    conversation: Conversation,
    user_message: str, 
    openAI: AsyncOpenAI,
    carrier: Dict[str, str]
) -> AsyncGenerator[str, None]:
    ctx = TraceContextTextMapPropagator().extract(carrier=carrier)
    with tracer.start_as_current_span('get_result', context=ctx):
        logger.info(f"get_result invoked for conversation={conversation.id}")
        try:
            response = await openAI.responses.create(
                conversation=conversation.id,
                input=[
                    {"role": "user", "content": user_message},
                ],
                extra_body={"agent": AgentReference(name=agent_name).as_dict()},
                stream=True
            )
            logger.info("Successfully created stream; starting to process events")
            output_message_id = ""
            input_created_at = datetime.now(timezone.utc).timestamp()
            async for event in response:
                print(event)
                if isinstance(event, ResponseCreatedEvent):
                    print(f"Stream response created with ID: {event.response.id}")
                elif isinstance(event, ResponseTextDeltaEvent):
                    print(f"Delta: {event.delta}")
                    stream_data = {'content': event.delta, 'type': "message"}
                    yield serialize_sse_event(stream_data)
                elif isinstance(event, ResponseOutputItemDoneEvent) and event.item.type == "message":
                    stream_data = await get_message_and_annotations(event.item)
                    stream_data['type'] = "completed_message"
                    output_message_id = event.item.id
                    yield serialize_sse_event(stream_data)                    
                elif isinstance(event, ResponseCompletedEvent):
                    print(f"Response completed with full message: {event.response.output_text}")
                    stream_data = {'type': "stream_end"}
                    yield serialize_sse_event(stream_data)           
                    
            # Save created_at timestamps in the background (non-blocking)
            asyncio.create_task(save_created_at(openAI, event.response, input_created_at, output_message_id))
                                 

        except Exception as e:
            logger.exception(f"Exception in get_result: {e}")
            yield serialize_sse_event({'type': "error", 'message': str(e)})


@router.get("/chat/history")
async def history(
    request: Request,
    agent: AgentVersionObject = Depends(get_agent_version_obj),
    openai_client : AsyncOpenAI = Depends(get_openai_client),
	_ = auth_dependency
):
    with tracer.start_as_current_span("chat_history"):
        conversation_id = request.cookies.get('conversation_id')
        agent_id = request.cookies.get('agent_id')

        # Get or create conversation using the reusable function
        conversation = await get_or_create_conversation(
            openai_client, conversation_id, agent_id, agent.id
        )
        agent_id = agent.id
    # Create a new message from the user's input.
    try:
        content = []
        messages = await openai_client.conversations.items.list(conversation_id=conversation.id, order="desc")
        async for message in messages:
            if isinstance(message, Message):
                formatteded_message = await get_message_and_annotations(message)
                formatteded_message['role'] = message.role
                formatteded_message['created_at'] = created_at.get(message.id, "")
                content.append(formatteded_message)


        logger.info(f"List message, conversation ID: {conversation_id}")
        response = JSONResponse(content=content)
    
        # Update cookies to persist the conversation IDs.
        response.set_cookie("conversation_id", conversation_id)
        response.set_cookie("agent_id", agent_id)
        return response
    except Exception as e:
        logger.error(f"Error listing message: {e}")
        raise HTTPException(status_code=500, detail=f"Error list message: {e}")

@router.get("/agent")
async def get_chat_agent(
    request: Request,
    agent: AgentVersionObject = Depends(get_agent_version_obj),
):
    return JSONResponse(content={"name": agent.name, "metadata": {"logo": agent.metadata.get("logo", "")}})

@router.post("/chat")
async def chat(
    request: Request,
    openai_client : AsyncOpenAI = Depends(get_openai_client),
    agent: AgentVersionObject = Depends(get_agent_version_obj),
    
    app_insights_conn_str : str = Depends(get_app_insights_conn_str),
	_ = auth_dependency
):
    # Retrieve the conversation ID from the cookies (if available).
    conversation_id = request.cookies.get('conversation_id')
    agent_id = request.cookies.get('agent_id')    

    with tracer.start_as_current_span("chat_request"):
        carrier = {}        
        TraceContextTextMapPropagator().inject(carrier)

        # if the connection no longer exist or agent is changed, create a new one
        conversation = await get_or_create_conversation(
            openai_client, conversation_id, agent_id, agent.id
        )
        conversation_id = conversation.id
        agent_id = agent.id
        
        # Parse the JSON from the request.
        try:
            user_message = await request.json()
        except Exception as e:
            logger.error(f"Invalid JSON in request: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid JSON in request: {e}")
        # Create a new message from the user's input.

        # Set the Server-Sent Events (SSE) response headers.
        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
        logger.info(f"Starting streaming response for conversation ID {conversation_id}")

        # Create the streaming response using the generator.
        response = StreamingResponse(get_result(agent.name, conversation, user_message.get('message', ''), openai_client, carrier), headers=headers)

        # Update cookies to persist the conversation and agent IDs.
        response.set_cookie("conversation_id", conversation_id)
        response.set_cookie("agent_id", agent_id)
        return response

def read_file(path: str) -> str:
    with open(path, 'r') as file:
        return file.read()


# def run_agent_evaluation(
#     thread_id: str, 
#     run_id: str,
#     ai_project: AIProjectClient,
#     app_insights_conn_str: str):

#     if app_insights_conn_str:
#         agent_evaluation_request = AgentEvaluationRequest(
#             run_id=run_id,
#             thread_id=thread_id,
#             evaluators={
#                 "Relevance": {"Id": EvaluatorIds.RELEVANCE.value},
#                 "TaskAdherence": {"Id": EvaluatorIds.TASK_ADHERENCE.value},
#                 "ToolCallAccuracy": {"Id": EvaluatorIds.TOOL_CALL_ACCURACY.value},
#             },
#             sampling_configuration=AgentEvaluationSamplingConfiguration(
#                 name="default",
#                 sampling_percent=100,
#             ),
#             redaction_configuration=AgentEvaluationRedactionConfiguration(
#                 redact_score_properties=False,
#             ),
#             app_insights_connection_string=app_insights_conn_str,
#         )
        
#         async def run_evaluation():
#             try:        
#                 logger.info(f"Running agent evaluation on thread ID {thread_id} and run ID {run_id}")
#                 agent_evaluation_response = await ai_project.evaluations.create_agent_evaluation(
#                     evaluation=agent_evaluation_request
#                 )
#                 logger.info(f"Evaluation response: {agent_evaluation_response}")
#             except Exception as e:
#                 logger.error(f"Error creating agent evaluation: {e}")

#         # Create a new task to run the evaluation asynchronously
#         asyncio.create_task(run_evaluation())


@router.get("/config/azure")
async def get_azure_config(_ = auth_dependency):
    """Get Azure configuration for frontend use"""
    try:
        subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID", "")
        tenant_id = os.environ.get("AZURE_TENANT_ID", "")
        resource_group = os.environ.get("AZURE_RESOURCE_GROUP", "")
        ai_project_resource_id = os.environ.get("AZURE_EXISTING_AIPROJECT_RESOURCE_ID", "")
        
        # Extract resource name and project name from the resource ID
        # Format: /subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.CognitiveServices/accounts/{resource}/projects/{project}
        resource_name = ""
        project_name = ""
        
        if ai_project_resource_id:
            parts = ai_project_resource_id.split("/")
            if len(parts) >= 8:
                resource_name = parts[8]  # accounts/{resource_name}
            if len(parts) >= 10:
                project_name = parts[10]  # projects/{project_name}
        
        return JSONResponse({
            "subscriptionId": subscription_id,
            "tenantId": tenant_id,
            "resourceGroup": resource_group,
            "resourceName": resource_name,
            "projectName": project_name,
            "wsid": ai_project_resource_id
        })
    except Exception as e:
        logger.error(f"Error getting Azure config: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Azure configuration")