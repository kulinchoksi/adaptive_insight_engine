import os
from aie_agents.workflow_orchestrator.agent import workflow_orchestrator_agent

# Alias for ADK compatibility
root_agent = workflow_orchestrator_agent

# Expose both for compatibility
__all__ = ["workflow_orchestrator_agent", "root_agent"]