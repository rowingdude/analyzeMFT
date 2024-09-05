import asyncio
from .windows_time import WindowsTime
from .mft_record import MftRecord
from .mft_analyzer import MftAnalyzer
from .file_writers import FileWriters
from .constants import VERSION, CSV_HEADER
from .cli import main as cli_main

def main():
    asyncio.run(cli_main())

__all__ = [
    'WindowsTime',
    'MftRecord',
    'MftAnalyzer',
    'FileWriters',
    'VERSION',
    'CSV_HEADER',
    'main'
]

__version__ = VERSION