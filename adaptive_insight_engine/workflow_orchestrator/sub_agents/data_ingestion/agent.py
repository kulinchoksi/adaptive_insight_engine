import os
from google.adk.agents import Agent
from .prompts import return_instructions_data_ingestion
from adaptive_insight_engine.tools import ingest_data
from utils import llm_factory

# TODO: Add actual tool functions for data ingestion

data_ingestion_agent = Agent(
    model=llm_factory.create_llm_client("DATA_INGESTION_AGENT_MODEL"),
    name="data_ingestion_agent",
    instruction=return_instructions_data_ingestion(),
    tools=[ingest_data],
    # Optionally add before_agent_callback, generate_content_config, etc.
) 