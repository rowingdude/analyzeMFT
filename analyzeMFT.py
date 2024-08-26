import asyncio
import logging
import sys
import time
import traceback
from typing import NoReturn, Callable, Any, Coroutine

from analyze_mft.parsers.mft_parser import MFTParser, parse_mft
from analyze_mft.utilities.file_handler import FileHandler
from analyze_mft.outputs.csv_writer import CSVWriter
from analyze_mft.parsers.options_parser import OptionsParser
from analyze_mft.utilities.logger import Logger
from analyze_mft.utilities.thread_manager import ThreadManager
from analyze_mft.outputs.json_writer import JSONWriter
from analyze_mft.utilities.error_handler import error_handler

class TimeoutError(Exception):
    pass

async def run_with_timeout(coro: Coroutine, timeout_duration: int = 300) -> Any:
    try:
        return await asyncio.wait_for(coro, timeout=timeout_duration)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Function call timed out after {timeout_duration} seconds")

@error_handler
async def initialize_components(options):
    print("Initializing components...")
    logger = Logger(options)
    print("Logger initialized")
    file_handler = FileHandler(options)
    print("File handler created")
    csv_writer = CSVWriter(options, file_handler)
    print("CSV writer created")
    json_writer = JSONWriter(options, file_handler)
    print("JSON writer created")
    thread_manager = ThreadManager(options.thread_count)
    print("Thread manager created")
   
    return logger, file_handler, csv_writer, json_writer, thread_manager

@error_handler
async def parse_mft(mft_parser: MFTParser) -> None:
    await mft_parser.generate_filepaths()
    await mft_parser.print_records()

async def main() -> NoReturn:
    try:
        options_parser = OptionsParser()
        options = options_parser.parse_options()

        print("Options parsed successfully")

        logger, file_handler, csv_writer, json_writer, thread_manager = await initialize_components(options)
        logger.info("Starting analyzeMFT")

        print("Components initialized")

        async with file_handler:
            logger.info("Opened input and output files successfully.")
            print("Files opened successfully")

            mft_parser = MFTParser(options, file_handler, csv_writer, json_writer, thread_manager)
            logger.info("Initializing the MFT parsing object...")
            print("MFT parser initialized")

            start_time = time.time()
            total_records = await mft_parser.get_total_records()
            logger.info(f"Total records: {total_records}")
            print(f"Total records: {total_records}")

            try:
                await run_with_timeout(parse_mft(mft_parser), timeout_duration=3600)  # 1 hour timeout
            except TimeoutError:
                logger.error("MFT parsing timed out after 1 hour")
                sys.exit(1)
            except Exception as e:
                logger.error(f"An error occurred during MFT parsing: {str(e)}")
                traceback.print_exc()
                sys.exit(1)

        end_time = time.time()
        logger.info(f"MFT parsing completed in {end_time - start_time:.2f} seconds")
        print("MFT parsing completed")

        logger.info("analyzeMFT completed successfully.")
        print("analyzeMFT completed successfully")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error in asyncio.run: {str(e)}")
        traceback.print_exc()