from .common_imports import *

class Logger:
    def __init__(self, options):
        self.options = options
        self.setup_logging()

    def setup_logging(self):
        log_level = logging.DEBUG if self.options.debug else logging.INFO
        logging.basicConfig(level=log_level,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            filename='analyzeMFT.log' if self.options.debug else None)
        if self.options.verbose:
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            formatter = logging.Formatter('%(levelname)s - %(message)s')
            console.setFormatter(formatter)
            logging.getLogger('').addHandler(console)

    @staticmethod
    def info(message):
        logging.info(message)

    @staticmethod
    def debug(message):
        logging.debug(message)

    @staticmethod
    def warning(message):
        logging.warning(message)

    @staticmethod
    def error(message):
        logging.error(message)
    
    @staticmethod
    def verbose(message):
        if logging.getLogger('').isEnabledFor(logging.INFO):
            print(message)