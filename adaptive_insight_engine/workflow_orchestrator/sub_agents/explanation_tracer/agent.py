import os
from google.adk.agents import Agent
from .prompts import return_instructions_explanation_tracer
from adaptive_insight_engine.tools import trace_explanation
from utils import llm_factory

explanation_tracer_agent = Agent(
    model=llm_factory.create_llm_client("EXPLANATION_TRACER_AGENT_MODEL"),
    name="explanation_tracer_agent",
    instruction=return_instructions_explanation_tracer(),
    tools=[trace_explanation],
    # Optionally add before_agent_callback, generate_content_config, etc.
) 