import os
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
# (plus your ComprehensiveDataAnalyzer and its input model here)

from google.adk.tools.crewai_tool import CrewaiTool
from .comprehensive_data_analyzer import ComprehensiveDataAnalyzer

# Instantiate your original CrewAI-based tool
data_analyzer = ComprehensiveDataAnalyzer()

# Wrap it for ADK
adk_data_analyzer = CrewaiTool(
    name="DataAnalyzer",
    description="Perform summary, stats, filter, correlation, group_by, time_series, and other analyses on CSV data.",
    tool=data_analyzer
)
