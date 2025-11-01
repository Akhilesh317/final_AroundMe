"""Structured logging configuration"""
import sys
from contextvars import ContextVar

import structlog
from loguru import logger

from app.config import settings

# Context variable for trace ID
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


def setup_logging():
    """Configure structured logging"""
    
    # Configure loguru
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
        level=settings.log_level,
        serialize=False,
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging_level=settings.log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
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