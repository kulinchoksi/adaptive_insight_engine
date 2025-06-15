import os
from google.adk.agents import Agent
from .prompts import return_instructions_explanation_tracer
from agents.tools import trace_explanation

explanation_tracer_agent = Agent(
    model=os.getenv("EXPLANATION_TRACER_AGENT_MODEL", "gemini-2.0-pro"),
    name="explanation_tracer_agent",
    instruction=return_instructions_explanation_tracer(),
    tools=[trace_explanation],
    # Optionally add before_agent_callback, generate_content_config, etc.
) 