import logging
from .constants import VERSION

class Logger:
    def __init__(self, options):
        self.options = options
        self.logger = self.setup_logging()

    def setup_logging(self):
        log_level = logging.DEBUG if self.options.debug else logging.INFO
        logger = logging.getLogger('analyzeMFT')
        logger.setLevel(log_level)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        if self.options.debug:
            file_handler = logging.FileHandler('analyzeMFT_debug.log')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        if self.options.verbose:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        return logger

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)