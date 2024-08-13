import argparse
import json
from typing import Dict, Any
from pathlib import Path

DEFAULT_CONFIG = {
    "debug": False,
    "localtz": None,
    "bodystd": False,
    "bodyfull": False,
    "json_output": False,
    "output_dir": "output",
    "csv_filename": "mft_output.csv",
    "bodyfile_name": "mft_bodyfile",
    "json_filename": "mft_output.json",
    "log_level": "INFO"
}

class Config:
    def __init__(self):
        self.parser = self.create_argument_parser()
        self.args = None
        self.config: Dict[str, Any] = DEFAULT_CONFIG.copy()

    def create_argument_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description="MFT Analyzer")
        parser.add_argument("input_file", help="Path to the MFT file to analyze")
        parser.add_argument("--config", help="Path to a JSON configuration file")
        parser.add_argument("--debug", action="store_true", help="Enable debug logging")
        parser.add_argument("--localtz", help="Use local timezone")
        parser.add_argument("--bodystd", action="store_true", help="Use standard body format")
        parser.add_argument("--bodyfull", action="store_true", help="Use full body format")
        parser.add_argument("--json", action="store_true", help="Output in JSON format")
        parser.add_argument("--output-dir", help="Directory for output files")
        parser.add_argument("--csv-filename", help="Name of the CSV output file")
        parser.add_argument("--bodyfile-name", help="Name of the body file")
        parser.add_argument("--json-filename", help="Name of the JSON output file")
        parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                            help="Set the logging level")
        return parser

    def load_config_file(self, config_file: str):
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                self.config.update(file_config)
        except json.JSONDecodeError:
            print(f"Error: The config file {config_file} is not valid JSON.")
            exit(1)
        except FileNotFoundError:
            print(f"Error: The config file {config_file} was not found.")
            exit(1)

    def parse_args(self):
        self.args = self.parser.parse_args()
        
        if self.args.config:
            self.load_config_file(self.args.config)

        # Override config with command-line arguments
        for arg, value in vars(self.args).items():
            if value is not None:
                self.config[arg] = value

    def get_config(self) -> Dict[str, Any]:
        return self.config