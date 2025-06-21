import os
from google.adk.agents import Agent
from .prompts import return_instructions_data_ingestion
from adaptive_insight_engine.tools import ingest_data

# TODO: Add actual tool functions for data ingestion

data_ingestion_agent = Agent(
    model=os.getenv("DATA_INGESTION_AGENT_MODEL", "gemini-2.0-pro"),
    name="data_ingestion_agent",
    instruction=return_instructions_data_ingestion(),
    tools=[ingest_data],
    # Optionally add before_agent_callback, generate_content_config, etc.
) 