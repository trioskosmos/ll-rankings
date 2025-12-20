# app/logging_config.py

import logging
import logging.handlers
from pathlib import Path

def setup_logging():
    """Configure logging for the application"""
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # File handler (all logs)
    fh = logging.handlers.RotatingFileHandler(
        logs_dir / "app.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )
    fh.setLevel(logging.DEBUG)
    
    # Console handler (warnings and above)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    root_logger.addHandler(fh)
    root_logger.addHandler(ch)
    
    return root_logger