import os
from google.adk.agents import Agent
from .prompts import return_instructions_insight_synthesis
from adaptive_insight_engine.tools import synthesize_insights

insight_synthesis_agent = Agent(
    model=os.getenv("INSIGHT_SYNTHESIS_AGENT_MODEL", "gemini-2.0-pro"),
    name="insight_synthesis_agent",
    instruction=return_instructions_insight_synthesis(),
    tools=[synthesize_insights],
    # Optionally add before_agent_callback, generate_content_config, etc.
) 