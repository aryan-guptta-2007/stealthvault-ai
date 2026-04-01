import logging
import sys
import os
import json
import traceback
import re
from datetime import datetime
from typing import Optional

# To be used for dynamic DB logging (initialized later to avoid circular imports)
_DB_LOG_FUNC = None

class SecretRedactionFilter(logging.Filter):
    """
    🛡️ ELITE REDACTION SHIELD
    Intercepts and masks potential secrets in log messages.
    """
    SENSITIVE_PATTERNS = [
        r'password["\']?\s*[:=]\s*["\']?([^"\'\s,]+)["\']?',
        r'token["\']?\s*[:=]\s*["\']?([^"\'\s,]+)["\']?',
        r'secret["\']?\s*[:=]\s*["\']?([^"\'\s,]+)["\']?',
        r'key["\']?\s*[:=]\s*["\']?([^"\'\s,]+)["\']?',
        r'authorization["\']?\s*[:]\s*Bearer\s+([^"\'\s,]+)',
        r'cookie["\']?\s*[:]\s*([^"\'\s,;]+)',
        r'postgres:\/\/([^:@]+):([^@]+)@', # DB Credentials
    ]

    def filter(self, record):
        msg = str(record.msg)
        for pattern in self.SENSITIVE_PATTERNS:
            msg = re.sub(pattern, lambda m: m.group(0).replace(m.group(1), "[REDACTED]"), msg, flags=re.IGNORECASE)
        record.msg = msg
        return True

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
    # 1. Base Configuration (Professional Structured Format)
    log_format = (
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    
    # 2. Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 🛡️ Apply Secret Redaction Filter
    redactor = SecretRedactionFilter()
    root_logger.addFilter(redactor)
    
    # HANDLERS
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(stream_handler)
    
    # 3. Add DB Handler for Errors
    db_handler = DatabaseLogHandler()
    db_handler.setLevel(logging.ERROR)
    root_logger.addHandler(db_handler)
    
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
