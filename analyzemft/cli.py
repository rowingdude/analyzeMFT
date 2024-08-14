import logging
from pathlib import Path
from .config import Config
from .mft_session import MftSession

def setup_logging(log_level: str):
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    logging.basicConfig(level=numeric_level, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    config = Config()
    config.parse_args()
    conf = config.get_config()

    setup_logging(conf['log_level'])

    session = MftSession(conf)
    
    try:
        session.open_files()
        session.process_mft_file()
        session.print_records()
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        session.close_files()

if __name__ == "__main__":
    main()