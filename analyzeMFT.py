import asyncio
import logging
import sys
from typing import NoReturn

from analyze_mft.parsers.mft_parser import MFTParser
from analyze_mft.utilities.file_handler import FileHandler, FileHandlerOptions
from analyze_mft.outputs.csv_writer import CSVWriter
from analyze_mft.parsers.options_parser import OptionsParser
from analyze_mft.utilities.logger import Logger, LoggerOptions
from analyze_mft.utilities.thread_manager import ThreadManager
from analyze_mft.outputs.json_writer import JSONWriter
from analyze_mft.outputs.body_writer import BodyFileWriter
from analyze_mft.outputs.csv_timeline import CSVTimelineWriter

async def initialize_components(options):
    logger = Logger(LoggerOptions(options.debug, options.verbose, options.log_file))
    file_handler = FileHandler(FileHandlerOptions(options.filename, options.output, options.bodyfile, options.csvtimefile))
    csv_writer = CSVWriter(options, file_handler)
    json_writer = JSONWriter(options, file_handler)
    body_writer = BodyfileWriter(options, file_handler) if options.bodyfile else None
    csv_timeline = CSVTimelineWriter(options, file_handler) if options.csvtimefile else None
    thread_manager = ThreadManager(options.thread_count)
   
    return logger, file_handler, csv_writer, json_writer, body_writer, csv_timeline, thread_manager

async def main() -> NoReturn:
    options_parser = OptionsParser()
    options = options_parser.parse_options()

    logger, file_handler, csv_writer, json_writer, body_writer, csv_timeline_writer, thread_manager = await initialize_components(options)
    logger.info("Starting analyzeMFT")

    async with file_handler:
        logger.info("Opened input and output files successfully.")
   
        mft_parser = MFTParser(options, file_handler, csv_writer, json_writer, thread_manager)
        logger.info("Initializing the MFT parsing object...")
       
        await mft_parser.parse_mft_file()

        if body_writer:
            await body_writer.write_records(mft_parser.mft)
        if csv_timeline:
            await csv_timeline.write_records(mft_parser.mft)

    await thread_manager.shutdown()
    logger.info("analyzeMFT completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())