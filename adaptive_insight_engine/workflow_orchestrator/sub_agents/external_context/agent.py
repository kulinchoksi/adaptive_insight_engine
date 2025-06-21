import os
from google.adk.agents import Agent
from .prompts import return_instructions_external_context
from adaptive_insight_engine.tools import fetch_external_data
from utils import llm_factory

# TODO: Add actual tool functions for external context

external_context_agent = Agent(
    model=llm_factory.create_llm_client("EXTERNAL_CONTEXT_AGENT_MODEL"),
    name="external_context_agent",
    instruction=return_instructions_external_context(),
    tools=[fetch_external_data],
    # Optionally add before_agent_callback, generate_content_config, etc.
) 