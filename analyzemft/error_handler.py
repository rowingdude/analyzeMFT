import logging
import sys
import traceback
from functools import wraps
from typing import Callable, Any, Type, Dict

class MFTAnalysisError(Exception):
    """Base exception for MFT analysis errors."""
    pass

class IOError(MFTAnalysisError):
    """Exception raised for I/O related errors."""
    pass

class ParsingError(MFTAnalysisError):
    """Exception raised for parsing related errors."""
    pass

class ConfigurationError(MFTAnalysisError):
    """Exception raised for configuration related errors."""
    pass

def setup_logging(log_level: str, log_file: str = None):
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    
    logging_config = {
        'level': numeric_level,
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S'
    }
    
    if log_file:
        logging_config['filename'] = log_file
        logging_config['filemode'] = 'a'
    
    logging.basicConfig(**logging_config)

def error_handler(error_map: Dict[Type[Exception], Type[MFTAnalysisError]] = None):
    if error_map is None:
        error_map = {}
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_type = type(e)
                if error_type in error_map:
                    raise error_map[error_type](str(e)) from e
                
                logging.error(f"Unhandled exception in {func.__name__}:")
                logging.error(traceback.format_exc())
                raise MFTAnalysisError(f"An unexpected error occurred in {func.__name__}: {str(e)}") from e
        return wrapper
    return decorator

def log_and_raise(exception: Type[Exception], message: str):
    """Log an error message and raise a specific exception."""
    logging.error(message)
    raise exception(message)

def handle_critical_error(e: Exception):
    """Handle critical errors that should terminate the program."""
    logging.critical(f"Critical error: {str(e)}")
    logging.critical(traceback.format_exc())
    sys.exit(1)