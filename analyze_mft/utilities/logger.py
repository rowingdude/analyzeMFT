import logging
from typing import Any, Optional
from dataclasses import dataclass
from pathlib import Path
from analyze_mft.constants.constants import VERSION

@dataclass
class LoggerOptions:
    debug: bool
    verbose: bool
    log_file: Optional[Path] = None

class Logger:
    def __init__(self, options: LoggerOptions):
        self.options = options
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger('analyzeMFT')
        logger.setLevel(logging.DEBUG if self.options.debug else logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        if self.options.debug and self.options.log_file:
            file_handler = logging.FileHandler(self.options.log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        if self.options.verbose:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        return logger

    async def initialize_components(options):
        logger = Logger(LoggerOptions(options.debug, options.verbose, 
                        Path(options.log_file) if options.log_file else None))

    def _log(self, level: int, message: str, *args: Any, **kwargs: Any) -> None:
        self.logger.log(level, message, *args, **kwargs)

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.DEBUG, message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.INFO, message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.WARNING, message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.ERROR, message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.CRITICAL, message, *args, **kwargs)

    @classmethod
    def get_version(cls) -> str:
        return VERSION