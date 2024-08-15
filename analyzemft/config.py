import argparse
from typing import Dict, Any
from dataclasses import dataclass, field

@dataclass
class Config:
    input_file: str = ""
    output_file: str = "mft_output.csv"
    output_format: str = "csv"
    log_level: str = "INFO"
    debug: bool = False
    local_timezone: bool = False
    anomaly_detection: bool = False
    reconstruct_paths: bool = True
    max_records: int = 15

    _parser: argparse.ArgumentParser = field(init=False, repr=False)

    def __post_init__(self):
        self._parser = self._create_argument_parser()

    def _create_argument_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description="MFT Analyzer")
        parser.add_argument("input_file", help="Path to the MFT file to analyze")
        parser.add_argument("--output", help="Output file path", default=self.output_file)
        parser.add_argument("--format", choices=["csv", "json"], default=self.output_format, help="Output format")
        parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default=self.log_level, help="Logging level")
        parser.add_argument("--debug", action="store_true", help="Enable debug mode")
        parser.add_argument("--local-timezone", action="store_true", help="Use local timezone for timestamps")
        parser.add_argument("--anomaly-detection", action="store_true", help="Enable anomaly detection")
        parser.add_argument("--no-path-reconstruction", action="store_false", dest="reconstruct_paths", help="Disable file path reconstruction")
        parser.add_argument("--max-records", type=int, default=0, help="Maximum number of records to process (0 for all)")
        return parser

    def parse_arguments(self) -> None:
        args = self._parser.parse_args()
        self.input_file = args.input_file
        self.output_file = args.output
        self.output_format = args.format
        self.log_level = args.log_level
        self.debug = args.debug
        self.local_timezone = args.local_timezone
        self.anomaly_detection = args.anomaly_detection
        self.reconstruct_paths = args.reconstruct_paths
        self.max_records = args.max_records

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_file": self.input_file,
            "output_file": self.output_file,
            "output_format": self.output_format,
            "log_level": self.log_level,
            "debug": self.debug,
            "local_timezone": self.local_timezone,
            "anomaly_detection": self.anomaly_detection,
            "reconstruct_paths": self.reconstruct_paths,
            "max_records": self.max_records,
        }

def get_config() -> Config:
    config = Config()
    config.parse_arguments()
    return config