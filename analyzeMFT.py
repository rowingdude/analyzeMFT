import sys 
try:

    from analyze_mft.mft_parser       import MFTParser
    from analyze_mft.file_handler     import FileHandler
    from analyze_mft.csv_writer       import CSVWriter
    from analyze_mft.options_parser   import OptionsParser
    from analyze_mft.attribute_parser import AttributeParser
    from analyze_mft.thread_manager   import ThreadManager
    from analyze_mft.logger           import Logger

except ImportError as e:
    print(f"Error: Failed to import required modules. {e}")
    sys.exit(1)

def main():

    options_parser = OptionsParser()
    options = options_parser.parse_options()

    logger = Logger(options)
    logger.info(f"Starting analyzeMFT")

    file_handler = FileHandler(options)
    file_handler.open_files()
    
    logger.info("Opened input and output files successfully.")

    csv_writer = CSVWriter(options, file_handler)

    with ThreadManager(options.thread_count) as thread_manager:

        logger.info("Initializing the MFT parsing object...")
        mft_parser = MFTParser(options, file_handler, csv_writer)
        
        logger.info("Running the MFT parser...")
        mft_parser.parse_mft_file()
        
        logger.info("Generating file paths...")
        mft_parser.generate_filepaths()
        
        logger.info("Writing records...")
        mft_parser.print_records()

    logger.info("analyzeMFT completed successfully.")

if __name__ == "__main__":
    main()