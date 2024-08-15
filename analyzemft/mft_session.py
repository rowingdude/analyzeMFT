import logging
import sys
import json
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
                self.file_csv = open(self.config['csv_filename'], 'w', newline='', encoding='utf-8')
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
                        try:
                            self.file_csv.write(','.join(csv_data) + '\n')
                        except UnicodeEncodeError as ue:
                            self.logger.warning(f"UnicodeEncodeError in record {i}: {ue}")
                            # Fall back to ASCII encoding, replacing non-ASCII characters
                            ascii_data = [item.encode('ascii', 'replace').decode('ascii') for item in csv_data]
                            self.file_csv.write(','.join(ascii_data) + '\n')
                        except Exception as e:
                            self.logger.error(f"Unexpected error writing record {i}: {e}")
                        self.file_csv.flush()
                    else:
                        self.logger.warning(f"Skipping record {i} due to formatting error: {csv_data[1]}")
                        try:
                            serializable_record = self._make_serializable(record)
                            self.logger.debug(f"Problematic record data: {json.dumps(serializable_record, default=str)}")
                        except Exception as e:
                            self.logger.error(f"Error serializing problematic record {i}: {e}")

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