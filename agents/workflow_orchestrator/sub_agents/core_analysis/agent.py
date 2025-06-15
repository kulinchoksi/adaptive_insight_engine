import os
from google.adk.agents import Agent
from .prompts import return_instructions_core_analysis
from agents.tools import analyze_data

# TODO: Add actual tool functions for core analysis

core_analysis_agent = Agent(
    model=os.getenv("CORE_ANALYSIS_AGENT_MODEL", "gemini-2.0-pro"),
    name="core_analysis_agent",
    instruction=return_instructions_core_analysis(),
    tools=[analyze_data],
    # Optionally add before_agent_callback, generate_content_config, etc.
) 