import os
from google.adk.agents import Agent
from .prompts import return_instructions_query_understanding
from adaptive_insight_engine.tools import understand_query

query_understanding_agent = Agent(
    model=os.getenv("QUERY_UNDERSTANDING_AGENT_MODEL", "gemini-2.0-pro"),
    name="query_understanding_agent",
    instruction=return_instructions_query_understanding(),
    tools=[understand_query],
    # Optionally add before_agent_callback, generate_content_config, etc.
) 