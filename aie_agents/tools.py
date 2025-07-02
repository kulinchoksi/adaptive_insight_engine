"""Tools for the Adaptive Insight Engine agents."""

import os
import logging
import uuid
import time
from datetime import datetime
from typing import Dict, Any, Optional, Union
import pandas as pd
import requests
from google.cloud import storage
from google.api_core import retry

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

# Structured logging formatter
class StructuredLogFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "trace_id": getattr(record, "trace_id", None),
        }
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        return str(log_data)

if os.getenv("ENABLE_STRUCTURED_LOGGING", "true").lower() == "true":
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredLogFormatter())
    logger.addHandler(handler)

class ToolError(Exception):
    """Base exception for tool errors."""
    def __init__(
        self,
        message: str,
        error_type: str,
        error_code: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.error_type = error_type
        self.error_code = error_code
        self.details = details or {}
        self.trace_id = str(uuid.uuid4())
        self.timestamp = datetime.utcnow().isoformat()
        super().__init__(message)

class InputValidationError(ToolError):
    """Raised when input validation fails."""
    def __init__(self, message: str, error_code: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "input_validation", error_code, details)

class ProcessingError(ToolError):
    """Raised when data processing fails."""
    def __init__(self, message: str, error_code: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "processing", error_code, details)

class ExternalServiceError(ToolError):
    """Raised when external service calls fail."""
    def __init__(self, message: str, error_code: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "external_service", error_code, details)

def log_tool_execution(func):
    """Decorator for logging tool execution."""
    def wrapper(*args, **kwargs):
        trace_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Log tool start
        logger.info(
            f"Tool execution started: {func.__name__}",
            extra={
                "trace_id": trace_id,
                "tool": func.__name__,
                "tool_args": str(args),
                "tool_kwargs": str(kwargs),
            }
        )
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log successful completion
            logger.info(
                f"Tool execution completed: {func.__name__}",
                extra={
                    "trace_id": trace_id,
                    "tool": func.__name__,
                    "execution_time": execution_time,
                    "status": "success",
                }
            )
            return result
            
        except ToolError as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Tool execution failed: {func.__name__}",
                extra={
                    "trace_id": trace_id,
                    "tool": func.__name__,
                    "execution_time": execution_time,
                    "error_type": e.error_type,
                    "error_code": e.error_code,
                    "details": e.details,
                }
            )
            return {
                "status": "error",
                "error_type": e.error_type,
                "error_code": e.error_code,
                "message": str(e),
                "details": {
                    "context": e.details,
                    "timestamp": e.timestamp,
                    "trace_id": e.trace_id,
                }
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Unexpected error in tool: {func.__name__}",
                extra={
                    "trace_id": trace_id,
                    "tool": func.__name__,
                    "execution_time": execution_time,
                    "error": str(e),
                },
                exc_info=True
            )
            return {
                "status": "error",
                "error_type": "system",
                "error_code": "unexpected_error",
                "message": "An unexpected error occurred",
                "details": {
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                    "trace_id": trace_id,
                }
            }
    
    return wrapper

@log_tool_execution
def ingest_data(file: Any, file_type: str) -> Dict[str, Any]:
    """
    Ingests and preprocesses the uploaded data file.
    
    Args:
        file: The uploaded file object.
        file_type: The type of file (csv, xlsx, pdf, etc.)
        
    Returns:
        dict: Metadata and cleaned data.
        
    Raises:
        InputValidationError: If file type is unsupported or file is invalid
        ProcessingError: If data processing fails
    """
    # Validate input
    if not file:
        raise InputValidationError(
            "No file provided",
            "missing_file",
            {"file_type": file_type}
        )
    
    if file_type not in ["csv", "xlsx", "xls"]:
        raise InputValidationError(
            f"Unsupported file type: {file_type}",
            "unsupported_file_type",
            {"file_type": file_type, "supported_types": ["csv", "xlsx", "xls"]}
        )
    
    try:
        # Read file based on type
        if file_type == "csv":
            df = pd.read_csv(file)
        else:  # xlsx or xls
            df = pd.read_excel(file)
            
        # Basic data cleaning
        df = df.dropna(how="all")
        df.columns = [c.strip() for c in df.columns]
        
        # Generate metadata
        metadata = {
            "columns": list(df.columns),
            "n_rows": len(df),
            "n_cols": len(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "missing_values": df.isnull().sum().to_dict(),
        }
        
        return {
            "status": "success",
            "data": df.to_dict(orient="records"),
            "metadata": metadata
        }
        
    except pd.errors.EmptyDataError:
        raise ProcessingError(
            "File is empty",
            "empty_file",
            {"file_type": file_type}
        )
    except pd.errors.ParserError as e:
        raise ProcessingError(
            f"Failed to parse file: {str(e)}",
            "parse_error",
            {"file_type": file_type, "error": str(e)}
        )
    except Exception as e:
        raise ProcessingError(
            f"Data processing failed: {str(e)}",
            "processing_error",
            {"file_type": file_type, "error": str(e)}
        )

@log_tool_execution
@retry.Retry()
def fetch_external_data(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetches and merges relevant external public data based on metadata.
    
    Args:
        metadata: Metadata from the primary dataset.
        
    Returns:
        dict: Merged external data.
        
    Raises:
        ExternalServiceError: If external API calls fail
        ProcessingError: If data processing fails
    """
    if not os.getenv("ENABLE_EXTERNAL_DATA", "true").lower() == "true":
        logger.warning("External data fetching is disabled")
        return {"status": "success", "external_data": None}
    
    try:
        location = metadata.get("location", "New York")
        logger.info(f"Fetching external data for location: {location}")
        
        # Example: Fetch weather data (replace with actual external data sources)
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": 40.71,
                "longitude": -74.01,
                "hourly": "temperature_2m"
            },
            timeout=int(os.getenv("REQUEST_TIMEOUT", "30"))
        )
        
        if response.status_code == 200:
            weather = response.json()
            return {"status": "success", "external_data": weather}
        else:
            raise ExternalServiceError(
                f"Failed to fetch external data: {response.status_code}",
                "api_error",
                {
                    "status_code": response.status_code,
                    "response": response.text,
                    "location": location
                }
            )
            
    except requests.Timeout:
        raise ExternalServiceError(
            "External data fetch timed out",
            "timeout",
            {"location": location}
        )
    except requests.RequestException as e:
        raise ExternalServiceError(
            f"Failed to fetch external data: {str(e)}",
            "request_error",
            {"location": location, "error": str(e)}
        )
    except Exception as e:
        raise ProcessingError(
            f"Error processing external data: {str(e)}",
            "processing_error",
            {"location": location, "error": str(e)}
        )

@log_tool_execution
def analyze_data(data: dict, external_data: dict = None) -> dict:
    """
    Performs core data analysis and correlation.
    Args:
        data: The processed primary dataset (list of dicts).
        external_data: Optional external data.
    Returns:
        dict: Analysis results.
    """
    try:
        df = pd.DataFrame(data)
        stats = df.describe(include="all").to_dict()
        # Optionally, merge and correlate with external_data
        return {"status": "success", "analysis": stats}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@log_tool_execution
def understand_query(query: str, context: dict = None) -> dict:
    """
    Interprets user's follow-up query and extracts parameters.
    Args:
        query: The user's follow-up query.
        context: Optional context.
    Returns:
        dict: Query type and parameters.
    """
    # Simple rule-based for demo; replace with LLM for production
    if "what if" in query.lower():
        return {"status": "success", "query_type": "what-if", "parameters": {}}
    else:
        return {"status": "success", "query_type": "data-retrieval", "parameters": {}}

@log_tool_execution
def run_simulation(scenario_params: dict) -> dict:
    """
    Runs a simulation based on scenario parameters.
    Args:
        scenario_params: Parameters for the scenario (expects 'data', 'column', 'percent_increase').
    Returns:
        dict: Simulation results.
    """
    try:
        data = scenario_params.get("data")
        column = scenario_params.get("column")
        percent = scenario_params.get("percent_increase", 0)
        if not data or not column:
            return {"status": "error", "message": "Missing data or column for simulation."}
        df = pd.DataFrame(data)
        if column not in df.columns:
            return {"status": "error", "message": f"Column {column} not found in data."}
        df[column] = df[column] * (1 + percent / 100.0)
        return {"status": "success", "simulation_result": df.to_dict(orient="records")}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@log_tool_execution
def synthesize_insights(analysis_results: dict, simulation_results: dict = None) -> dict:
    """
    Synthesizes findings and generates insights/narratives.
    Args:
        analysis_results: Results from core analysis.
        simulation_results: Optional simulation results.
    Returns:
        dict: Synthesized insights.
    """
    # Placeholder: In production, call LLM (e.g., Gemini via Vertex AI)
    try:
        summary = f"Analysis summary: {str(analysis_results)}"
        if simulation_results:
            summary += f"\nSimulation results: {str(simulation_results)}"
        return {"status": "success", "insights": summary}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@log_tool_execution
def trace_explanation(events: list) -> Dict[str, Any]:
    """
    Collects and formats explanations for insights.
    
    Args:
        events: List of events/logs from agents.
        
    Returns:
        dict: Explanation trace.
        
    Raises:
        ProcessingError: If explanation processing fails
    """
    if not os.getenv("ENABLE_EXPLANATION_TRACING", "true").lower() == "true":
        logger.warning("Explanation tracing is disabled")
        return {"status": "success", "explanation": "Explanation tracing disabled"}
    
    try:
        # Process and format events
        formatted_events = []
        for event in events:
            if isinstance(event, dict):
                formatted_events.append(
                    f"[{event.get('timestamp', 'N/A')}] "
                    f"{event.get('agent', 'Unknown')}: "
                    f"{event.get('message', 'No message')}"
                )
            else:
                formatted_events.append(str(event))
        
        explanation = "\n".join(formatted_events)
        
        # Store explanation if enabled
        if os.getenv("ENABLE_METRICS", "true").lower() == "true":
            try:
                storage_client = storage.Client()
                bucket = storage_client.bucket(os.getenv("STORAGE_BUCKET"))
                blob = bucket.blob(f"explanations/{datetime.utcnow().isoformat()}.txt")
                blob.upload_from_string(explanation)
            except Exception as e:
                logger.warning(f"Failed to store explanation: {str(e)}")
        
        return {"status": "success", "explanation": explanation}
        
    except Exception as e:
        raise ProcessingError(
            f"Failed to process explanation: {str(e)}",
            "explanation_error",
            {"error": str(e)}
        ) 