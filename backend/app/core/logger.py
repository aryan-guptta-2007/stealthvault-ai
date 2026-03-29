import logging
import sys
import os
import json
import traceback
from datetime import datetime
from typing import Optional

# To be used for dynamic DB logging (initialized later to avoid circular imports)
_DB_LOG_FUNC = None

class DatabaseLogHandler(logging.Handler):
    """
    Custom Logging Handler that pushes critical/error events to the StealthVault DB.
    """
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            global _DB_LOG_FUNC
            if _DB_LOG_FUNC:
                try:
                    # Extract stack trace if available
                    stack_trace = None
                    if record.exc_info:
                        stack_trace = "".join(traceback.format_exception(*record.exc_info))
                    
                    # Call the async persistence function (fire and forget)
                    import asyncio
                    message = self.format(record)
                    # Get tenant_id from record extras if available
                    tenant_id = getattr(record, 'tenant_id', 'system')
                    
                    # metadata
                    metadata = {
                        "filename": record.pathname,
                        "lineno": record.lineno,
                        "funcName": record.funcName,
                        "process": record.process,
                        "thread": record.thread
                    }
                    
                    _DB_LOG_FUNC(
                        level=record.levelname,
                        component=record.name,
                        message=message,
                        tenant_id=tenant_id,
                        stack_trace=stack_trace,
                        metadata=metadata
                    )
                except Exception as e:
                    # Fallback to stderr if DB logging fails
                    sys.stderr.write(f"⚠️ Logger: Database Persistence Failed: {e}\n")

def setup_logging(level=logging.INFO):
    """
    Sets up the global logging configuration for StealthVault AI.
    """
    # 1. Base Configuration
    log_format = (
        " [%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s "
    )
    
    # 2. Configure root logger
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # 3. Add DB Handler for Errors
    db_handler = DatabaseLogHandler()
    db_handler.setLevel(logging.ERROR)
    logging.getLogger().addHandler(db_handler)
    
    # 4. Silence noisy third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    print(f"✅ System Observability Initialized (Level: {logging.getLevelName(level)})")

def set_db_logger(log_func):
    """Called after app startup to link the logger to the database persistence layer."""
    global _DB_LOG_FUNC
    _DB_LOG_FUNC = log_func

# Accessor for convenience
logger = logging.getLogger("stealthvault")
