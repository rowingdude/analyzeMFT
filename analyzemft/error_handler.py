
import logging
from typing import Callable, Any

class MFTAnalysisError(Exception):          pass
class FileOperationError(MFTAnalysisError): pass
class ParsingError(MFTAnalysisError):       pass
class ConfigurationError(MFTAnalysisError): pass

def setup_logging(log_level: str, log_file: str = None) -> None:
    
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ConfigurationError(f'Invalid log level: {log_level}')
    
    logging_config = {
        'level': numeric_level,
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S'
    }
    
    if log_file:
        logging_config['filename'] = log_file
        logging_config['filemode'] = 'a'
    
    logging.basicConfig(**logging_config)

def error_handler(func: Callable) -> Callable:
   
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except FileOperationError as e:
            logging.error(f"File operation error in {func.__name__}: {str(e)}")
            raise
        except ParsingError as e:
            logging.error(f"Parsing error in {func.__name__}: {str(e)}")
            raise
        except ConfigurationError as e:
            logging.error(f"Configuration error in {func.__name__}: {str(e)}")
            raise
        except Exception as e:
            logging.exception(f"Unexpected error in {func.__name__}: {str(e)}")
            raise MFTAnalysisError(f"An unexpected error occurred in {func.__name__}") from e
    return wrapper