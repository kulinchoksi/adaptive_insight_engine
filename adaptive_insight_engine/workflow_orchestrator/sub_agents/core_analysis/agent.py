import os
from google.adk.agents import Agent
from .prompts import return_instructions_core_analysis
from .tools import describe_dataframe, find_anomalies
from adaptive_insight_engine.tools import analyze_data

# TODO: Add actual tool functions for core analysis

core_analysis_agent = Agent(
    model=os.getenv("CORE_ANALYSIS_AGENT_MODEL", "gemini-2.0-pro"),
    name="core_analysis_agent",
    instruction=return_instructions_core_analysis(),
    tools=[
        describe_dataframe,    # Tool: Descriptive statistics and info
        find_anomalies,        # Tool: Find outliers/anomalies in data
        analyze_data           # Tool: Core analysis logic
    ],
)