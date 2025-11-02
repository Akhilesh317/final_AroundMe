"""Structured logging configuration"""
import sys
from contextvars import ContextVar

import structlog
from loguru import logger

from app.config import settings

# Context variable for trace ID
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


def setup_logging():
    """Configure structured logging with loguru and structlog"""
    log_level = settings.log_level.upper()
    
    # Configure loguru
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=log_level,
    )
    
    # Configure structlog with simpler configuration
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    """Get a logger instance"""
    return structlog.get_logger(name)


def set_trace_id(trace_id: str):
    """Set trace ID for current context"""
    trace_id_var.set(trace_id)
    structlog.contextvars.bind_contextvars(trace_id=trace_id)


def get_trace_id() -> str:
    """Get current trace ID"""
    return trace_id_var.get()