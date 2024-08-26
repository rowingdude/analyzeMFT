"""
analyze_mft - A Python package for analyzing MFT (Master File Table) files.

This package provides tools and utilities for parsing, analyzing, and extracting
information from MFT files in NTFS file systems.

Modules:
    parsers: Contains modules for parsing MFT records and command-line options.
    utilities: Provides utility classes and functions for file handling, logging, etc.
    outputs: Includes modules for writing output in various formats (CSV, JSON).
    constants: Defines constants used throughout the package.

For more information, please refer to the documentation or visit:
https://github.com/rowingdude/analyzeMFT
"""

from analyze_mft.constants.constants import VERSION

__version__ = VERSION
__author__ = "Benjamin Cance"
__email__ = "bjc@tdx.li"
__license__ = "MIT"

# Import main components for easier access
from analyze_mft.parsers.mft_parser import MFTParser
from analyze_mft.parsers.options_parser import OptionsParser
from analyze_mft.utilities.file_handler import FileHandler
from analyze_mft.utilities.logger import Logger
from analyze_mft.outputs.csv_writer import CSVWriter
from analyze_mft.outputs.json_writer import JSONWriter

# Define what should be imported with "from analyze_mft import *"
__all__ = [
    'MFTParser',
    'OptionsParser',
    'FileHandler',
    'Logger',
    'CSVWriter',
    'JSONWriter',
]

# Optionally, you can include a setup function here if needed
def setup():
    # ToDo set up the environment 
    pass  

# You can also include a cleanup function if necessary
def cleanup():
    # ToDo - clean up the environment
    pass  # Add cleanup logic if needed