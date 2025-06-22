import os
from google.adk.agents import Agent
from .prompts import return_instructions_workflow_orchestrator
from .sub_agents.data_ingestion.agent import data_ingestion_agent
from .sub_agents.external_context.agent import external_context_agent
from .sub_agents.core_analysis.agent import core_analysis_agent
from .sub_agents.query_understanding.agent import query_understanding_agent
from .sub_agents.simulation.agent import simulation_agent
from .sub_agents.insight_synthesis.agent import insight_synthesis_agent
from .sub_agents.explanation_tracer.agent import explanation_tracer_agent

workflow_orchestrator_agent = Agent(
    model=os.getenv("WORKFLOW_ORCHESTRATOR_AGENT_MODEL", "gemini-2.0-pro"),
    name="workflow_orchestrator_agent",
    instruction=return_instructions_workflow_orchestrator(),
    sub_agents=[
        data_ingestion_agent,
        external_context_agent,
        core_analysis_agent,
        query_understanding_agent,
        simulation_agent,
        insight_synthesis_agent,
        explanation_tracer_agent,
    ],
    # No tools: rely on sub-agents for orchestration
)