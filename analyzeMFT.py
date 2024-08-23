#!/usr/bin/env python3

import sys
from typing import NoReturn
import logging
from functools import wraps

try:
    from analyze_mft.mft_parser import MFTParser
    from analyze_mft.file_handler import FileHandler
    from analyze_mft.csv_writer import CSVWriter
    from analyze_mft.options_parser import OptionsParser
    from analyze_mft.logger import Logger
    from analyze_mft.thread_manager import ThreadManager
    from analyze_mft.json_writer import JSONWriter
    
except ImportError as e:
    print(f"Error: Failed to import required modules. {e}")
    sys.exit(1)

def error_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"An error occurred in {func.__name__}: {str(e)}")
            sys.exit(1)
    return wrapper

@error_handler
def initialize_components(options):
    logger = Logger(options)
    file_handler = FileHandler(options)
    csv_writer = CSVWriter(options, file_handler)
    json_writer = JSONWriter(options, file_handler)
    thread_manager = ThreadManager(options.thread_count)
    
    return logger, file_handler, csv_writer, json_writer, thread_manager

@error_handler
def parse_mft(mft_parser: MFTParser) -> None:
    mft_parser.parse_mft_file()
    mft_parser.generate_filepaths()
    mft_parser.print_records()

def main() -> NoReturn:
    options_parser = OptionsParser()
    options = options_parser.parse_options()

    logger, file_handler, csv_writer, json_writer, thread_manager = initialize_components(options)

    logger.info("Starting analyzeMFT")

    with file_handler:
        logger.info("Opened input and output files successfully.")

        mft_parser = MFTParser(options, file_handler, csv_writer, json_writer, thread_manager)
        
        logger.info("Initializing the MFT parsing object...")
        parse_mft(mft_parser)

    logger.info("analyzeMFT completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()