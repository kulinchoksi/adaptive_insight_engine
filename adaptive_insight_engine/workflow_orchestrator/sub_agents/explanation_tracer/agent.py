import os
from google.adk.agents import Agent
from .prompts import return_instructions_explanation_tracer
from adaptive_insight_engine.tools import trace_explanation
from utils import agent_log_tracer

explanation_tracer_agent = Agent(
    model=os.getenv("EXPLANATION_TRACER_AGENT_MODEL", "gemini-2.0-flash-lite-001"),
    name="explanation_tracer_agent",
    instruction=return_instructions_explanation_tracer(),
    tools=[trace_explanation],
    before_model_callback=agent_log_tracer.before_model_callback,
    after_model_callback=agent_log_tracer.after_model_callback,
    before_agent_callback=agent_log_tracer.before_agent_callback,
    after_agent_callback=agent_log_tracer.after_agent_callback,
    before_tool_callback=agent_log_tracer.before_tool_modifier,
    after_tool_callback=agent_log_tracer.after_too_callback,
)