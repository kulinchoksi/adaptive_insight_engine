"""Logging configuration for the Adaptive Insight Engine."""

import os
import logging
import structlog
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from functools import wraps

# Configure base logging
def configure_logging():
    """Configure the logging system with structured logging support."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "json").lower()
    
    # Configure basic logging
    logging.basicConfig(
        format="%(message)s",
        stream=None,
        level=getattr(logging, log_level),
    )
    
    # Configure structlog
    processors = [
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        add_trace_id,
        add_agent_context,
        structlog.processors.JSONRenderer() if log_format == "json" else structlog.dev.ConsoleRenderer(),
    ]
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure log storage if enabled
    if os.getenv("ENABLE_LOG_STORAGE", "false").lower() == "true":
        log_path = os.getenv("LOG_STORAGE_PATH", "logs")
        os.makedirs(log_path, exist_ok=True)
        file_handler = logging.FileHandler(
            os.path.join(log_path, f"app_{datetime.now().strftime('%Y%m%d')}.log")
        )
        file_handler.setFormatter(logging.Formatter("%(message)s"))
        logging.getLogger().addHandler(file_handler)

def add_trace_id(logger: structlog.BoundLogger, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add a trace ID to the log event if not present."""
    if "trace_id" not in event_dict:
        event_dict["trace_id"] = str(uuid.uuid4())
    return event_dict

def add_agent_context(logger: structlog.BoundLogger, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add agent context to the log event if available."""
    if hasattr(logger, "context"):
        event_dict.update(logger.context)
    return event_dict

class AgentLogger:
    """Logger wrapper for agent-specific logging."""
    
    def __init__(self, agent_name: str, **context):
        self.agent_name = agent_name
        self.logger = structlog.get_logger(agent_name)
        self.context = {
            "agent": agent_name,
            "timestamp": datetime.utcnow().isoformat(),
            **context
        }
    
    def bind(self, **kwargs) -> "AgentLogger":
        """Bind additional context to the logger."""
        self.context.update(kwargs)
        return self
    
    def _log(self, level: str, event: str, **kwargs) -> None:
        """Log an event with the current context."""
        self.logger.bind(**self.context).log(level, event, **kwargs)
    
    def debug(self, event: str, **kwargs) -> None:
        self._log("debug", event, **kwargs)
    
    def info(self, event: str, **kwargs) -> None:
        self._log("info", event, **kwargs)
    
    def warning(self, event: str, **kwargs) -> None:
        self._log("warning", event, **kwargs)
    
    def error(self, event: str, **kwargs) -> None:
        self._log("error", event, **kwargs)
    
    def critical(self, event: str, **kwargs) -> None:
        self._log("critical", event, **kwargs)

def log_execution(logger: Optional[AgentLogger] = None):
    """Decorator for logging function execution."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = AgentLogger(func.__module__)
            
            trace_id = str(uuid.uuid4())
            start_time = datetime.utcnow()
            
            logger.bind(
                trace_id=trace_id,
                function=func.__name__,
                start_time=start_time.isoformat()
            ).info("function_start", args=str(args), kwargs=str(kwargs))
            
            try:
                result = func(*args, **kwargs)
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()
                
                logger.bind(
                    trace_id=trace_id,
                    function=func.__name__,
                    end_time=end_time.isoformat(),
                    duration=duration
                ).info("function_end", result=str(result))
                
                return result
                
            except Exception as e:
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()
                
                logger.bind(
                    trace_id=trace_id,
                    function=func.__name__,
                    end_time=end_time.isoformat(),
                    duration=duration,
                    error_type=type(e).__name__,
                    error=str(e)
                ).error("function_error", exc_info=True)
                
                raise
        
        return wrapper
    return decorator

def get_agent_logger(agent_name: str, **context) -> AgentLogger:
    """Get a logger instance for an agent."""
    return AgentLogger(agent_name, **context)

# Initialize logging when module is imported
configure_logging() 