import os
from google.adk.agents import Agent
from .prompts import return_instructions_data_ingestion
from .tools import parse_uploaded_file, validate_dataframe
from adaptive_insight_engine.tools import ingest_data

# TODO: Add actual tool functions for data ingestion

data_ingestion_agent = Agent(
    model=os.getenv("DATA_INGESTION_AGENT_MODEL", "gemini-2.0-pro"),
    name="data_ingestion_agent",
    instruction=return_instructions_data_ingestion(),
    tools=[
        parse_uploaded_file,    # Tool: Parse uploaded files (CSV, Excel)
        validate_dataframe      # Tool: Validate and summarize dataframe
    ],
)