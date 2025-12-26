# logger.py - Centralized Logging Configuration
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from config import LOG_LEVEL, LOG_DIR, LOG_FILE_MAX_BYTES, LOG_BACKUP_COUNT

# Ensure log directory exists
LOG_DIR.mkdir(exist_ok=True)

# Color codes for console output
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)

def setup_logger(name, log_file=None, level=None):
    """
    Setup logger with file and console handlers
    
    Args:
        name: Logger name (usually __name__)
        log_file: Log file name (optional, defaults to {name}.log)
        level: Log level (optional, defaults to config.LOG_LEVEL)
    
    Returns:
        logging.Logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Set log level
    log_level = getattr(logging, level or LOG_LEVEL)
    logger.setLevel(log_level)
    
    # Format
    file_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = ColoredFormatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler with rotation
    if log_file is None:
        log_file = f"{name.replace('.', '_')}.log"
    
    file_handler = RotatingFileHandler(
        LOG_DIR / log_file,
        maxBytes=LOG_FILE_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger

# Pre-configured loggers for different modules
def get_gateway_logger():
    return setup_logger('gateway', 'gateway.log')

def get_dashboard_logger():
    return setup_logger('dashboard', 'dashboard.log')

def get_simulator_logger():
    return setup_logger('simulator', 'simulator.log')

def get_database_logger():
    return setup_logger('database', 'database.log')

# Example usage
if __name__ == "__main__":
    logger = setup_logger(__name__, 'test.log')
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    print(f"\n✅ Logs written to: {LOG_DIR / 'test.log'}")
