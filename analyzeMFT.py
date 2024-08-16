try:

    from analyze_mft.common_imports import *
    from analyze_mft.mft_parser import MFTParser
    from analyze_mft.file_handler import FileHandler
    from analyze_mft.csv_writer import CSVWriter
    from analyze_mft.options_parser import OptionsParser
    from analyze_mft.attribute_parser import AttributeParser
    from analyze_mft.thread_manager import ThreadManager

except ImportError as e:
    print(f"Error: Failed to import required modules. {e}")
    sys.exit(1)

def main():
    options_parser = OptionsParser()
    options = options_parser.parse_options()

    file_handler = FileHandler(options)
    file_handler.open_files()

    csv_writer = CSVWriter(options, file_handler)

    with ThreadManager(options.thread_count) as thread_manager:
        mft_parser = MFTParser(options, file_handler, csv_writer)
        mft_parser.parse_mft_file()
        mft_parser.generate_filepaths()
        mft_parser.print_records()

if __name__ == "__main__":
    main()