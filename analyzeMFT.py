import logging
import sys
import time
from functools import wraps
from tqdm import tqdm
from typing import NoReturn, Callable, Any
import signal

import threading

class TimeoutError(Exception):
    pass


async def run_with_timeout(coro: Coroutine, timeout_duration: int = 300) -> Any:
    try:
        return await asyncio.wait_for(coro, timeout=timeout_duration)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Function call timed out after {timeout_duration} seconds")

    result = []
    def worker():
        try:
            result.append(func(*args, **kwargs))
        except Exception as e:
            result.append(e)

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join(timeout_duration)
    if thread.is_alive():
        raise TimeoutError(f"Function call timed out after {timeout_duration} seconds")
    if result and isinstance(result[0], Exception):
        raise result[0]
    return result[0] if result else None
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
def parse_mft(mft_parser: MFTParser, progress_callback: Callable[[int], None]) -> None:
    mft_parser.parse_mft_file(progress_callback)
    mft_parser.generate_filepaths()
    mft_parser.print_records()

async def main() -> NoReturn:
    options_parser = OptionsParser()
    options = options_parser.parse_options()

    logger, file_handler, csv_writer, json_writer, thread_manager = initialize_components(options)
    logger.info("Starting analyzeMFT")

    async with file_handler:
        logger.info("Opened input and output files successfully.")
   
        mft_parser = MFTParser(options, file_handler, csv_writer, json_writer, thread_manager)
       
        logger.info("Initializing the MFT parsing object...")
       
        start_time = time.time()
        total_records = await mft_parser.get_total_records()  
       
        with tqdm(total=total_records, desc="Parsing MFT") as pbar:
            def update_progress(records_processed):
                pbar.update(records_processed - pbar.n)
           
            try:
                await run_with_timeout(parse_mft(mft_parser, update_progress), timeout_duration=3600)  # 1 hour timeout
            except TimeoutError:
                logger.error("MFT parsing timed out after 1 hour")
                sys.exit(1)
            except Exception as e:
                logger.error(f"An error occurred during MFT parsing: {str(e)}")
                sys.exit(1)
       
        end_time = time.time()
        logger.info(f"MFT parsing completed in {end_time - start_time:.2f} seconds")

    logger.info("analyzeMFT completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())