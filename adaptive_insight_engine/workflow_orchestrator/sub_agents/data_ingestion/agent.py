import os
from google.adk.agents import Agent
from .prompts import return_instructions_data_ingestion
from .tools import parse_uploaded_file, validate_dataframe
from adaptive_insight_engine.tools import ingest_data
from utils import agent_log_tracer

# TODO: Add actual tool functions for data ingestion

data_ingestion_agent = Agent(
    model=os.getenv("DATA_INGESTION_AGENT_MODEL", "gemini-2.0-flash-lite-001"),
    name="data_ingestion_agent",
    instruction=return_instructions_data_ingestion(),
    tools=[
        parse_uploaded_file,    # Tool: Parse uploaded files (CSV, Excel)
        validate_dataframe      # Tool: Validate and summarize dataframe
    ],
    before_model_callback=agent_log_tracer.before_model_callback,
    after_model_callback=agent_log_tracer.after_model_callback,
    before_agent_callback=agent_log_tracer.before_agent_callback,
    after_agent_callback=agent_log_tracer.after_agent_callback,
    before_tool_callback=agent_log_tracer.before_tool_modifier,
    after_tool_callback=agent_log_tracer.after_too_callback,
)