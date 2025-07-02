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
from utils import agent_log_tracer
from google.adk.agents import SequentialAgent



workflow_orchestrator_agent = SequentialAgent(
    # model=os.getenv("WORKFLOW_ORCHESTRATOR_AGENT_MODEL", "gemini-2.0-flash-lite-001"),
    name="workflow_orchestrator_agent",
    description="You are a sequential agent, You have to invoke each agents one by one, and then provide the final output.",
    sub_agents=[
        data_ingestion_agent,
        core_analysis_agent
    ],
    before_agent_callback=agent_log_tracer.before_agent_callback,
    after_agent_callback=agent_log_tracer.after_agent_callback,
    # No tools: rely on sub-agents for orchestration
)

# workflow_orchestrator_agent = Agent(
#     model=os.getenv("WORKFLOW_ORCHESTRATOR_AGENT_MODEL", "gemini-2.0-flash-lite-001"),
#     name="workflow_orchestrator_agent",
#     instruction=return_instructions_workflow_orchestrator(),
#     sub_agents=[
#         data_ingestion_agent,
#         external_context_agent,
#         core_analysis_agent,
#         query_understanding_agent,
#         simulation_agent,
#         insight_synthesis_agent,
#         explanation_tracer_agent,
#     ],
#     before_model_callback=agent_log_tracer.before_model_callback,
#     after_model_callback=agent_log_tracer.after_model_callback,
#     before_agent_callback=agent_log_tracer.before_agent_callback,
#     after_agent_callback=agent_log_tracer.after_agent_callback,
#     before_tool_callback=agent_log_tracer.before_tool_modifier,
#     after_tool_callback=agent_log_tracer.after_tool_callback,
#     # No tools: rely on sub-agents for orchestration
# )