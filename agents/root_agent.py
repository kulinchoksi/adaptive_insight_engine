import os
from google.adk.agents import Agent
from agents.user_interaction.agent import user_interaction_agent
from agents.workflow_orchestrator.agent import workflow_orchestrator_agent

root_agent = Agent(
    model=os.getenv("ROOT_AGENT_MODEL", "gemini-2.0-pro"),
    name="adaptive_insight_root_agent",
    description="Root agent orchestrating the Adaptive Insight Engine multi-agent workflow.",
    instruction="You are the root orchestrator. Delegate to the user interaction and workflow orchestrator agents as needed to fulfill user requests.",
    sub_agents=[
        user_interaction_agent,
        workflow_orchestrator_agent,
    ],
    tools=[],  # Add any root-level tools if needed
) 