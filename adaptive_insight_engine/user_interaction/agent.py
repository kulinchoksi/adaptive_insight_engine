# (Moved from agents/user_interaction_agent.py)
import os
from google.adk.agents import Agent
from .prompts import return_instructions_user_interaction

user_interaction_agent = Agent(
    model=os.getenv("USER_INTERACTION_AGENT_MODEL", "gemini-2.0-pro"),
    name="user_interaction_agent",
    instruction=return_instructions_user_interaction(),
    sub_agents=[],
    tools=[],
) 