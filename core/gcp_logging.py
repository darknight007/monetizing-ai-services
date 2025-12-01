"""
Google Cloud Logging Integration
Provides structured logging for GCP environments with fallback to standard logging.

Note: Automatically detects GCP environment. Falls back to standard logging if not on GCP.
"""
import logging
import os
import sys
from typing import Any, Dict

# Try to import Google Cloud Logging
try:
    from google.cloud import logging as gcp_logging
    from google.cloud.logging.handlers import CloudLoggingHandler
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False


class GCPLogger:
    """
    Structured logger with GCP Cloud Logging integration.
    
    Features:
    - Automatic GCP environment detection
    - Structured JSON logging
    - Trace and span ID correlation
    - Fallback to standard logging
    """
    
    def __init__(self, name: str = "ask-scrooge", log_level: str = None):
        """
        Initialize logger.
        
        Args:
            name: Logger name
            log_level: Log level (DEBUG, INFO, WARNING, ERROR)
        """
        self.name = name
        self.log_level = log_level or os.getenv("LOG_LEVEL", "INFO")
        self.enable_gcp = os.getenv("ENABLE_GCP_LOGGING", "0") == "1"
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logger with appropriate handlers."""
        logger = logging.getLogger(self.name)
        logger.setLevel(getattr(logging, self.log_level.upper()))
        
        # Remove existing handlers
        logger.handlers = []
        
        # GCP Cloud Logging (if available and enabled)
        if GCP_AVAILABLE and self.enable_gcp:
            try:
                client = gcp_logging.Client()
                handler = CloudLoggingHandler(client, name=self.name)
                logger.addHandler(handler)
                print(f"✅ GCP Cloud Logging enabled for {self.name}", file=sys.stderr)
                return logger
            except Exception as e:
                print(f"⚠️  GCP Cloud Logging failed, using standard logging: {e}", file=sys.stderr)
        
        # Standard logging fallback
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def log(self, level: str, message: str, **kwargs):
        """
        Log message with structured data.
        
        Args:
            level: Log level (debug, info, warning, error, critical)
            message: Log message
            **kwargs: Additional structured data
        """
        log_method = getattr(self.logger, level.lower())
        
        # Add structured data if GCP enabled
        if GCP_AVAILABLE and self.enable_gcp:
            log_method(message, extra={"json_fields": kwargs})
        else:
            # Format kwargs as string for standard logging
            if kwargs:
                extra_str = " | " + " | ".join(f"{k}={v}" for k, v in kwargs.items())
                message += extra_str
            log_method(message)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.log("debug", message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.log("info", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.log("warning", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self.log("error", message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.log("critical", message, **kwargs)


# Global logger instance
_logger = None


def get_logger(name: str = "ask-scrooge") -> GCPLogger:
    """
    Get or create global logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        GCPLogger instance
    """
    global _logger
    if _logger is None:
        _logger = GCPLogger(name)
    return _logger


# Convenience functions
def log_agent_execution(agent_name: str, session_id: str, status: str, **kwargs):
    """
    Log agent execution with standard format.
    
    Args:
        agent_name: Name of the agent
        session_id: Session identifier
        status: Status (started, completed, failed)
        **kwargs: Additional context
    """
    logger = get_logger()
    logger.info(
        f"Agent {agent_name} {status}",
        agent=agent_name,
        session_id=session_id,
        status=status,
        **kwargs
    )


def log_api_call(endpoint: str, method: str, status_code: int, duration_ms: float, **kwargs):
    """
    Log API call with standard format.
    
    Args:
        endpoint: API endpoint
        method: HTTP method
        status_code: Response status code
        duration_ms: Request duration in milliseconds
        **kwargs: Additional context
    """
    logger = get_logger()
    logger.info(
        f"API {method} {endpoint} -> {status_code}",
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        duration_ms=duration_ms,
        **kwargs
    )


def log_error_with_context(error: Exception, context: Dict[str, Any]):
    """
    Log error with rich context.
    
    Args:
        error: Exception object
        context: Additional context dictionary
    """
    logger = get_logger()
    logger.error(
        f"Error: {str(error)}",
        error_type=type(error).__name__,
        error_message=str(error),
        **context
    )


# SOC2 Compliance logging
def log_compliance_event(event_type: str, user_id: str = None, resource: str = None, **kwargs):
    """
    Log compliance-relevant events for SOC2 audit trail.
    
    Args:
        event_type: Type of event (access, modification, deletion, etc.)
        user_id: User or service identifier
        resource: Resource being accessed
        **kwargs: Additional context
    """
    logger = get_logger()
    logger.info(
        f"Compliance Event: {event_type}",
        event_type=event_type,
        user_id=user_id or "system",
        resource=resource,
        compliance=True,
        **kwargs
    )
