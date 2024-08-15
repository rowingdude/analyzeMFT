import csv
import json
import logging

from typing import Dict, Any, List, TextIO
from mft_core import MFTRecord
from mft_reference import MFTReference
from config import Config


class MFTOutputFormatter:
    @staticmethod
    def to_csv(record: MFTRecord) -> List[str]:
        data = record.parsed_data
        
        def format_time(timestamp):
            if timestamp == 0:
                return "Not set"
            dt = MFTReference.windows_time_to_datetime(timestamp)
            return str(dt) if dt else "Invalid Timestamp"

        return [
            str(data.get('recordnum', '')),
            'Active' if record.is_active else 'Inactive',
            record.record_type,
            data.get('filename', ''),
            format_time(data.get('si', {}).get('crtime', 0)),
            format_time(data.get('si', {}).get('mtime', 0)),
            format_time(data.get('si', {}).get('atime', 0)),
            str(data.get('bytes_in_use', 0)),
        ]
    
    @staticmethod
    def to_json(record: MFTRecord) -> str:
        return json.dumps(record.parsed_data, default=str)


class MFTOutputSession:
    def __init__(self, config: Config):
        self.config = config
        self.output_file: TextIO = open(config.output_file, 'w', newline='', encoding='utf-8')
        self.formatter = MFTOutputFormatter()
        self.csv_writer = csv.writer(self.output_file) if config.output_format == 'csv' else None

    def write_record(self, record: MFTRecord):
        try:
            if self.config.output_format == 'csv':
                self.csv_writer.writerow(self.formatter.to_csv(record))
            elif self.config.output_format == 'json':
                self.output_file.write(self.formatter.to_json(record) + '\n')
            logging.info(f"Written record {record.parsed_data.get('recordnum', 'unknown')}")
        except Exception as e:
            logging.error(f"Error writing record: {e}")

    def close(self):
        self.output_file.close()