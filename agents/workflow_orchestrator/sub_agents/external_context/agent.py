import os
from google.adk.agents import Agent
from .prompts import return_instructions_external_context
from agents.tools import fetch_external_data

# TODO: Add actual tool functions for external context

external_context_agent = Agent(
    model=os.getenv("EXTERNAL_CONTEXT_AGENT_MODEL", "gemini-2.0-pro"),
    name="external_context_agent",
    instruction=return_instructions_external_context(),
    tools=[fetch_external_data],
    # Optionally add before_agent_callback, generate_content_config, etc.
) 