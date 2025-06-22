import os
from google.adk.agents import Agent
from .prompts import return_instructions_external_context
from adaptive_insight_engine.tools import fetch_external_data
from utils import agent_log_tracer

external_context_agent = Agent(
    model=os.getenv("EXTERNAL_CONTEXT_AGENT_MODEL", "gemini-2.0-flash-lite-001"),
    name="external_context_agent",
    instruction=return_instructions_external_context(),
    tools=[fetch_external_data],
    before_model_callback=agent_log_tracer.before_model_callback,
    after_model_callback=agent_log_tracer.after_model_callback,
    before_agent_callback=agent_log_tracer.before_agent_callback,
    after_agent_callback=agent_log_tracer.after_agent_callback,
    before_tool_callback=agent_log_tracer.before_tool_modifier,
    after_tool_callback=agent_log_tracer.after_too_callback,
    # Optionally add before_agent_callback, generate_content_config, etc.
)