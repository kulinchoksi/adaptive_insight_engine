import os
from google.adk.agents import Agent
from .prompts import return_instructions_core_analysis
from .tools import describe_dataframe, find_anomalies
from adaptive_insight_engine.tools import analyze_data
from utils import agent_log_tracer
from google.adk.tools.crewai_tool import CrewaiTool
from .data_tools import adk_data_analyzer

# TODO: Add actual tool functions for core analysis

# crewai_tool = CrewaiTool(
#     name="ComprehensiveDataAnalyzer",
#     description="Analyze the complete dataset from a CSV file (provided as content string or path) to ensure ALL records are included. This tool provides direct access to the entire dataset.",
#     tool=comprehensive_data_analyzer.ComprehensiveDataAnalyzer
# ),

core_analysis_agent = Agent(
    model=os.getenv("CORE_ANALYSIS_AGENT_MODEL", "gemini-2.0-flash-lite-001"),
    name="core_analysis_agent",
    instruction=return_instructions_core_analysis(),
    tools=[
        adk_data_analyzer
        # describe_dataframe,    # Tool: Descriptive statistics and info
        # find_anomalies,        # Tool: Find outliers/anomalies in data
        # analyze_data           # Tool: Core analysis logic
    ],
    before_model_callback=agent_log_tracer.before_model_callback,
    after_model_callback=agent_log_tracer.after_model_callback,
    before_agent_callback=agent_log_tracer.before_agent_callback,
    after_agent_callback=agent_log_tracer.after_agent_callback,
    before_tool_callback=agent_log_tracer.before_tool_modifier,
    after_tool_callback=agent_log_tracer.after_too_callback,
)