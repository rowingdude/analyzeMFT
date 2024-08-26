import asyncio
import sys
from typing import NoReturn

from analyze_mft.parsers.mft_parser import MFTParser
from analyze_mft.utilities.file_handler import FileHandler, FileHandlerOptions
from analyze_mft.outputs.csv_writer import CSVWriter
from analyze_mft.outputs.json_writer import JSONWriter
from analyze_mft.outputs.body_writer import BodyFileWriter
from analyze_mft.outputs.csv_timeline import CSVTimelineWriter
from analyze_mft.parsers.options_parser import OptionsParser
from analyze_mft.utilities.logger import setup_logging, LoggerOptions, get_logger


async def initialize_components(options):
    logger = setup_logging(LoggerOptions(options.debug, options.verbose, options.log_file))
    file_handler = await FileHandler(FileHandlerOptions(
        options.filename, options.output, options.bodyfile, options.csvtimefile
    )).__aenter__()
    csv_writer = CSVWriter(options, file_handler)
    json_writer = JSONWriter(options, file_handler)
    body_writer = BodyFileWriter(options, file_handler) if options.bodyfile else None
    csv_timeline = CSVTimelineWriter(options, file_handler) if options.csvtimefile else None
    
   
    return logger, file_handler, csv_writer, json_writer, body_writer, csv_timeline

async def main() -> NoReturn:
    options_parser = OptionsParser()
    options = options_parser.parse_options()

    logger, file_handler, csv_writer, json_writer, body_writer, csv_timeline_writer = \
        await initialize_components(options)

    try:
        logger.info("Starting analyzeMFT")
        logger.info("Opened input and output files successfully.")
   
        mft_parser = MFTParser(options, file_handler, csv_writer, json_writer)
        logger.info("Initializing the MFT parsing object...")
       
        await mft_parser.parse_mft_file()
        
        if body_writer:
            await body_writer.write_records(mft_parser.mft)
        
        if csv_timeline_writer:
            await csv_timeline_writer.write_records(mft_parser.mft)

    except Exception as e:
        logger.error(f"An error occurred during MFT parsing: {str(e)}")
        sys.exit(1)
    finally:
        await file_handler.__aexit__(None, None, None)
    
    logger.info("analyzeMFT completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOperation interrupted by user. Exiting.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)