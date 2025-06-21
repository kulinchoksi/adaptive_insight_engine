import os
from google.adk.agents import Agent
from .prompts import return_instructions_query_understanding
from adaptive_insight_engine.tools import understand_query
from utils import llm_factory

query_understanding_agent = Agent(
    model=llm_factory.create_llm_client("QUERY_UNDERSTANDING_AGENT_MODEL"),
    name="query_understanding_agent",
    instruction=return_instructions_query_understanding(),
    tools=[understand_query],
    # Optionally add before_agent_callback, generate_content_config, etc.
) 