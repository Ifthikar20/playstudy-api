import logging
import json
import sys
from typing import Dict, Any
import uuid
from datetime import datetime
from app.core.config import get_settings

settings = get_settings()


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    def format(self, record):
        log_record: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "request_id": getattr(record, "request_id", str(uuid.uuid4())),
        }
        
        # Add exception info if available
        if record.exc_info:
            exception_type = record.exc_info[0].__name__ if record.exc_info[0] else ""
            exception_value = str(record.exc_info[1]) if record.exc_info[1] else ""
            log_record["exception"] = {
                "type": exception_type,
                "message": exception_value,
            }

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in (
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "id", "levelname", "levelno", "lineno", "module",
                "msecs", "message", "msg", "name", "pathname", "process",
                "processName", "relativeCreated", "stack_info", "thread", "threadName",
                "taskName"  # Exclude taskName to prevent conflicts
            ):
                log_record[key] = value
        
        return json.dumps(log_record)


def setup_logging() -> None:
    """Configure logging for the application"""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JsonFormatter())

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)
    root_logger.addHandler(console_handler)

    # Configure application loggers
    app_logger = logging.getLogger("app")
    app_logger.setLevel(log_level)
    
    # Configure third-party loggers
    for logger_name in ["uvicorn", "fastapi"]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)