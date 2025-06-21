import os
from google.adk.agents import Agent
from adaptive_insight_engine.user_interaction.agent import user_interaction_agent
from adaptive_insight_engine.workflow_orchestrator.agent import workflow_orchestrator_agent
from utils import llm_factory

root_agent = Agent(
    model=llm_factory.create_llm_client("ROOT_AGENT_MODEL"),
    name="adaptive_insight_root_agent",
    description="Root agent orchestrating the Adaptive Insight Engine multi-agent workflow.",
    instruction="You are the root orchestrator. Delegate to the user interaction and workflow orchestrator agents as needed to fulfill user requests.",
    sub_agents=[
        user_interaction_agent,
        workflow_orchestrator_agent,
    ],
    tools=[],  # Add any root-level tools if needed
) 