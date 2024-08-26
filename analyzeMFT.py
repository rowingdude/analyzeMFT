import asyncio
import logging
import sys
import time
from functools import wraps
from typing import NoReturn, Any

from analyze_mft.parsers.mft_parser import MFTParser
from analyze_mft.utilities.file_handler import FileHandler
from analyze_mft.outputs.csv_writer import CSVWriter
from analyze_mft.parsers.options_parser import OptionsParser
from analyze_mft.utilities.logger import Logger
from analyze_mft.utilities.thread_manager import ThreadManager
from analyze_mft.outputs.json_writer import JSONWriter
from analyze_mft.outputs.body_file_writer import BodyFileWriter
from analyze_mft.outputs.csv_timeline_writer import CSVTimelineWriter

class TimeoutError(Exception):
    pass

async def run_with_timeout(coro, timeout_duration: int = 3600):
    try:
        return await asyncio.wait_for(coro, timeout=timeout_duration)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Function call timed out after {timeout_duration} seconds")

async def initialize_components(options):
    logger = Logger(options)
    file_handler = FileHandler(options)
    csv_writer = CSVWriter(options, file_handler)
    json_writer = JSONWriter(options, file_handler)
    body_writer = BodyFileWriter(options, file_handler) if options.bodyfile else None
    csv_timeline_writer = CSVTimelineWriter(options, file_handler) if options.csvtimefile else None
    thread_manager = ThreadManager(options.thread_count)
   
    return logger, file_handler, csv_writer, json_writer, body_writer, csv_timeline_writer, thread_manager

async def main() -> NoReturn:
    options_parser = OptionsParser()
    options = options_parser.parse_options()

    logger, file_handler, csv_writer, json_writer, body_writer, csv_timeline_writer, thread_manager = await initialize_components(options)
    logger.info("Starting analyzeMFT")

    async with file_handler:
        logger.info("Opened input and output files successfully.")
   
        mft_parser = MFTParser(options, file_handler, csv_writer, json_writer, thread_manager)
       
        logger.info("Initializing the MFT parsing object...")
       
        start_time = time.time()
        
        try:
            await run_with_timeout(mft_parser.parse_mft_file(), timeout_duration=3600)  # 1 hour timeout
        except TimeoutError:
            logger.error("MFT parsing timed out after 1 hour")
            sys.exit(1)
        except Exception as e:
            logger.error(f"An error occurred during MFT parsing: {str(e)}")
            sys.exit(1)
       
        end_time = time.time()
        logger.info(f"MFT parsing completed in {end_time - start_time:.2f} seconds")

        if body_writer:
            await body_writer.write_records(mft_parser.mft)
        if csv_timeline_writer:
            await csv_timeline_writer.write_records(mft_parser.mft)

    logger.info("analyzeMFT completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())