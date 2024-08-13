import argparse
import logging
from typing import Dict, Any
from . import mft_utils
from .mft_formatters import mft_to_csv, mft_to_body, mft_to_l2t, mft_to_json
from .mft_utils import decodeMFTmagic, decodeMFTisactive, decodeMFTrecordtype, decodeVolumeInfo, decodeObjectID, ObjectID

def set_default_options() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MFT Analyzer")
    parser.add_argument("--debug", action="store_true", default=False, help="Enable debug logging")
    parser.add_argument("--localtz", default=None, help="Use local timezone")
    parser.add_argument("--bodystd", action="store_true", default=False, help="Use standard body format")
    parser.add_argument("--bodyfull", action="store_true", default=False, help="Use full body format")
    parser.add_argument("--json", action="store_true", default=False, help="Output in JSON format")
    return parser

def setup_logging(debug: bool):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

def read_mft_file(filename: str) -> bytes:
    try:
        with open(filename, 'rb') as file:
            return file.read(1024)
    except IOError as e:
        logging.error(f"Error reading MFT file: {e}")
        raise
