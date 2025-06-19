# (Moved from agents/user_interaction_agent.py)
import os
from google.adk.agents import Agent
from .prompts import return_instructions_user_interaction
from utils import llm_factory

user_interaction_agent = Agent(
    model=llm_factory.create_llm_client("USER_INTERACTION_AGENT_MODEL"),
    name="user_interaction_agent",
    instruction=return_instructions_user_interaction(),
    sub_agents=[],
    tools=[],
) 