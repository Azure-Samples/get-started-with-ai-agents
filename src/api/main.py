# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

import contextlib
import logging
import os
import sys
import json
from typing import Dict, Optional

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import FilePurpose, FileSearchTool, AsyncToolSet, FileSearchToolResource
from azure.identity import DefaultAzureCredential

import fastapi
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from logging_config import configure_logging

enable_trace = False
logger = None

@contextlib.asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    agent = None

    try:
        ai_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(exclude_shared_token_cache_credential=True),
            conn_str=os.environ["AZURE_AIPROJECT_CONNECTION_STRING"],
        )
        logger.info("Created AIProjectClient")

        if enable_trace:
            application_insights_connection_string = ""
            try:
                application_insights_connection_string = await ai_client.telemetry.get_connection_string()
            except Exception as e:
                e_string = str(e)
                logger.error("Failed to get Application Insights connection string, error: %s", e_string)
            if not application_insights_connection_string:
                logger.error("Application Insights was not enabled for this project.")
                logger.error("Enable it via the 'Tracing' tab in your AI Foundry project page.")
                exit()
            else:
                from azure.monitor.opentelemetry import configure_azure_monitor
                configure_azure_monitor(connection_string=application_insights_connection_string)
                ai_client.telemetry.enable()
                logger.info("Configured Application Insights for tracing.")

                app_config_endpoint = os.getenv("APP_CONFIGURATION_ENDPOINT")
                if app_config_endpoint:
                    try: 
                        from azure.appconfiguration.provider.aio import load
                        from featuremanagement.aio import FeatureManager
                        from featuremanagement.azuremonitor import publish_telemetry                    
                        app_config = await load(
                            endpoint=app_config_endpoint,
                            credential=DefaultAzureCredential(),
                            feature_flag_enabled=True,
                            feature_flag_refresh_enabled=True,
                            refresh_interval=300 # no refresh within 5 mins to avoid throttling
                        )
                        feature_manager = FeatureManager(app_config, on_feature_evaluated=publish_telemetry)
                        app.state.app_config = app_config
                        app.state.feature_manager = feature_manager
                        logger.info("Configured App Configuration with feature flag support.")
                    except ModuleNotFoundError:
                        logger.warning("Required libraries for App Configuration not installed.")
                        logger.warning("Please make sure azure-appconfiguration-provider and FeatureManagement are installed.")
                    except Exception as e:
                        logger.warning("Failed to setup App Configuration", exc_info=True)

        if os.environ.get("AZURE_AI_AGENT_ID"):
            try: 
                agent = await ai_client.agents.get_agent(os.environ["AZURE_AI_AGENT_ID"])
                logger.info("Agent already exists, skipping creation")
                logger.info(f"Fetched agent, agent ID: {agent.id}")
                logger.info(f"Fetched agent, model name: {agent.model}")
            except Exception as e:
                logger.error(f"Error fetching agent: {e}", exc_info=True)

        if not agent:
            # Fallback to searching by name
            agent_name = os.environ["AZURE_AI_AGENT_NAME"]
            agent_list = await ai_client.agents.list_agents()
            if agent_list.data:
                for agent_object in agent_list.data:
                    if agent_object.name == agent_name:
                        agent = agent_object
                        logger.info(f"Found agent by name '{agent_name}', ID={agent_object.id}")
                        break

        if not agent:
            raise RuntimeError("No agent found. Ensure qunicorn.py created one or set AZURE_AI_AGENT_ID.")

        app.state.ai_client = ai_client
        app.state.agent = agent
        
        yield

    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        raise RuntimeError(f"Error during startup: {e}")

    finally:
        try:
            await ai_client.close()
            logger.info("Closed AIProjectClient")
        except Exception as e:
            logger.error("Error closing AIProjectClient", exc_info=True)


def create_app():
    if not os.getenv("RUNNING_IN_PRODUCTION"):
        load_dotenv(override=True)

    global logger
    logger = configure_logging(os.getenv("APP_LOG_FILE", ""))

    enable_trace_string = os.getenv("ENABLE_AZURE_MONITOR_TRACING", "")
    global enable_trace
    enable_trace = False
    if enable_trace_string == "":
        enable_trace = False
    else:
        enable_trace = str(enable_trace_string).lower() == "true"
    if enable_trace:
        logger.info("Tracing is enabled.")
        try:
            from azure.monitor.opentelemetry import configure_azure_monitor
        except ModuleNotFoundError:
            logger.error("Required libraries for tracing not installed.")
            logger.error("Please make sure azure-monitor-opentelemetry is installed.")
            exit()
    else:
        logger.info("Tracing is not enabled")

    directory = os.path.join(os.path.dirname(__file__), "static")
    app = fastapi.FastAPI(lifespan=lifespan)
    app.mount("/static", StaticFiles(directory=directory), name="static")

    from . import routes  # Import routes
    app.include_router(routes.router)

    # Global exception handler for any unhandled exceptions
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception occurred", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    return app
