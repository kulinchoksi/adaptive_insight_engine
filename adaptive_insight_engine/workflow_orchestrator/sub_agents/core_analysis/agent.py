import os
from google.adk.agents import Agent
from .prompts import return_instructions_core_analysis
from adaptive_insight_engine.tools import analyze_data
from utils import llm_factory

# TODO: Add actual tool functions for core analysis

core_analysis_agent = Agent(
    model=llm_factory.create_llm_client("CORE_ANALYSIS_AGENT_MODEL"),
    name="core_analysis_agent",
    instruction=return_instructions_core_analysis(),
    tools=[analyze_data],
    # Optionally add before_agent_callback, generate_content_config, etc.
) 