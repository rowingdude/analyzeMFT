import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, IO
from .mft_analyzer import MFTAnalyzer
from .mft_formatters import mft_to_csv, mft_to_body, mft_to_l2t, mft_to_json
from analyzemft.error_handler import error_handler, FileOperationError, ParsingError, MFTAnalysisError

class MftSession:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mft: Dict[int, Dict[str, Any]] = {}
        self.folders: Dict[str, str] = {}
        self.file_mft: Optional[IO] = None
        self.file_csv: Optional[IO] = None
        self.file_body: Optional[IO] = None
        self.file_json: Optional[IO] = None
        self.file_csv_time: Optional[IO] = None
        self.analyzer: Optional[MFTAnalyzer] = None
        self.logger = logging.getLogger(__name__)

    @error_handler
    def open_files(self) -> None:
        try:
            self.file_mft = open(self.config['input_file'], 'rb')
        except IOError as e:
            raise FileOperationError(f"Unable to open input file: {self.config['input_file']}") from e

        if self.config.get('csv_filename'):
            try:
                self.file_csv = open(self.config['csv_filename'], 'w', newline='')
            except IOError as e:
                raise FileOperationError(f"Unable to open CSV output file: {self.config['csv_filename']}") from e


    @error_handler
    def process_mft_file(self) -> None:
        try:
            self.analyzer = MFTAnalyzer(self.config)
            self.analyzer.process_mft_file(self.file_mft)
            self.mft = self.analyzer.mft
            self.folders = self.analyzer.folders
        except Exception as e:
            raise ParsingError("Error processing MFT file") from e
                
    @error_handler
    def print_records(self) -> None:
        try:
            for i, record in self.mft.items():
                if self.file_csv:
                    csv_data = mft_to_csv(record, False)
                    if csv_data[0] != "Error":
                        self.file_csv.write(','.join(csv_data) + '\n')
                        self.file_csv.flush()
                    else:
                        self.logger.warning(f"Skipping record {i} due to formatting error: {csv_data[1]}")
                if self.file_csv_time:
                    self.file_csv_time.write(mft_to_l2t(record))
                if self.file_body:
                    self.file_body.write(mft_to_body(record, self.config.get('bodyfull', False), self.config.get('bodystd', False)))
                if self.config.get('json'):
                    print(mft_to_json(record))

        except IOError as e:
            raise FileOperationError("Error writing output") from e

    @error_handler
    def close_files(self) -> None:
        files_to_close = [
            ('MFT file', self.file_mft),
            ('CSV file', self.file_csv),
            ('Body file', self.file_body),
            ('CSV time file', self.file_csv_time)
        ]
        for file_name, file in files_to_close:
            if file:
                try:
                    file.close()
                except Exception as e:
                    self.logger.error(f"Error closing {file_name}: {e}")

    def run(self) -> None:
        try:
            self.open_files()
            self.process_mft_file()
            self.print_records()
        except MFTAnalysisError as e:
            self.logger.error(f"An error occurred during MFT analysis: {e}")
            raise
        finally:
            self.close_files()