import os
from google.adk.agents import Agent
from .prompts import return_instructions_query_understanding
from aie_agents.tools import understand_query
from utils import agent_log_tracer

query_understanding_agent = Agent(
    model=os.getenv("QUERY_UNDERSTANDING_AGENT_MODEL", "gemini-2.0-flash-lite-001"),
    name="query_understanding_agent",
    instruction=return_instructions_query_understanding(),
    tools=[understand_query],
    before_model_callback=agent_log_tracer.before_model_callback,
    after_model_callback=agent_log_tracer.after_model_callback,
    before_agent_callback=agent_log_tracer.before_agent_callback,
    after_agent_callback=agent_log_tracer.after_agent_callback,
    before_tool_callback=agent_log_tracer.before_tool_modifier,
    after_tool_callback=agent_log_tracer.after_tool_callback,
)