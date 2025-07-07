import asyncio
import csv
import io
import logging
import os
import signal
import sqlite3
import sys
import traceback
from typing import Dict, Set, List, Optional, Any
from .constants import *
from .mft_record import MftRecord
from .file_writers import FileWriters

class MftAnalyzer:
    def __init__(self, mft_file: str, output_file: str, debug: int = 0, verbosity: int = 0, 
                 compute_hashes: bool = False, export_format: str = "csv") -> None:
        self.mft_file = mft_file
        self.output_file = output_file
        self.debug = debug
        self.verbosity = int(verbosity) 
        self.compute_hashes = compute_hashes
        self.export_format = export_format
        self.csvfile = None
        self.csv_writer = None
        self.interrupt_flag = asyncio.Event()
        self.setup_logging()
        self.setup_interrupt_handler()
        
        self.mft_records = {}
        self.stats = {
            'total_records': 0,
            'active_records': 0,
            'directories': 0,
            'files': 0,
        }
        if self.compute_hashes:
            self.stats.update({
                'unique_md5': set(),
                'unique_sha256': set(),
                'unique_sha512': set(),
                'unique_crc32': set(),
            })

    def setup_logging(self) -> None:
        """Get logger and configure level based on verbosity and debug levels."""
        # Get logger (configuration should be done by CLI)
        self.logger = logging.getLogger('analyzeMFT')
        
        # Set log level based on verbosity and debug if not already configured
        if not self.logger.handlers:
            # Fallback configuration if no handlers exist
            logging.basicConfig(
                level=logging.WARNING,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        # Adjust level based on verbosity settings
        if self.debug >= 2:
            self.logger.setLevel(logging.DEBUG)
        elif self.debug >= 1 or self.verbosity >= 2:
            self.logger.setLevel(logging.INFO)
        elif self.verbosity >= 1:
            self.logger.setLevel(logging.WARNING)
        else:
            self.logger.setLevel(logging.ERROR)
        
        # Optionally add file handler for debug mode
        if self.debug >= 1 and not any(isinstance(h, logging.FileHandler) for h in self.logger.handlers):
            file_handler = logging.FileHandler(f"{self.output_file}.log")
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def setup_interrupt_handler(self):
        def interrupt_handler(signum, frame):
            self.logger.warning("Interrupt received. Cleaning up...")
            self.interrupt_flag.set()

        if sys.platform == "win32": # Windows is evil ...
            import win32api
            win32api.SetConsoleCtrlHandler(lambda x: interrupt_handler(None, None), True)

        else: # On a proper operating system ...
            signal.signal(signal.SIGINT, interrupt_handler)
            signal.signal(signal.SIGTERM, interrupt_handler)

    def log(self, message: str, level: int = 0):
        """Legacy log method for backwards compatibility."""
        if level == 0:
            self.logger.error(message)
        elif level == 1:
            self.logger.warning(message)
        elif level == 2:
            self.logger.info(message)
        else:
            self.logger.debug(message)

    async def analyze(self) -> None:
        try:
            self.logger.warning("Starting MFT analysis...")
            self.initialize_csv_writer()
            await self.process_mft()
            await self.write_output()
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")
            if self.debug:
                self.logger.debug("Full traceback:", exc_info=True)
        finally:
            if self.csvfile:
                self.csvfile.close()
            if self.interrupt_flag.is_set():
                self.logger.warning("Analysis interrupted by user.")
            else:
                self.logger.warning("Analysis complete.")
            self.print_statistics()


    async def process_mft(self) -> None:
        self.logger.warning(f"Processing MFT file: {self.mft_file}")
        try:
            with open(self.mft_file, 'rb') as f:
                while not self.interrupt_flag.is_set():
                    raw_record = await self.read_record(f) 
                    if not raw_record:
                        break

                    try:
                        self.logger.info(f"Processing record {self.stats['total_records']}")
                        record = MftRecord(raw_record, self.compute_hashes, self.debug, self.logger)
                        self.logger.info(f"Record parsed, recordnum: {record.recordnum}")
                        self.stats['total_records'] += 1
                        
                        if record.flags & FILE_RECORD_IN_USE:
                            self.stats['active_records'] += 1
                        if record.flags & FILE_RECORD_IS_DIRECTORY:
                            self.stats['directories'] += 1
                        else:
                            self.stats['files'] += 1

                        self.mft_records[record.recordnum] = record

                        if self.debug >= 2:
                            self.logger.info(f"Processed record {self.stats['total_records']}: {record.filename}")
                        elif self.stats['total_records'] % 10000 == 0:
                            self.logger.warning(f"Processed {self.stats['total_records']} records...")

                        if self.stats['total_records'] % 1000 == 0:
                            await self.write_csv_block()
                            self.mft_records.clear()
                            
                        if self.interrupt_flag.is_set():
                            self.logger.warning("Interrupt detected. Stopping processing.")
                            break

                    except Exception as e:
                        self.logger.warning(f"Error processing record {self.stats['total_records']}: {str(e)}")
                        self.logger.info(f"Raw record (first 100 bytes): {raw_record[:100].hex()}")
                        if self.debug >= 2:
                            self.logger.debug("Full traceback:", exc_info=True)
                        continue

        except Exception as e:
            self.logger.error(f"Error reading MFT file: {str(e)}")
            if self.debug >= 1:
                self.logger.debug("Full traceback:", exc_info=True)

        self.logger.error(f"MFT processing complete. Total records processed: {self.stats['total_records']}")

    async def read_record(self, file):
        return file.read(MFT_RECORD_SIZE)

    def handle_interrupt(self) -> None:
        if sys.platform == "win32":
            # Windows-specific interrupt handling
            import win32api
            def windows_handler(type):
                self.interrupt_flag.set()
                self.logger.warning("\nCtrl+C pressed. Cleaning up and writing data...")
                return True
            win32api.SetConsoleCtrlHandler(windows_handler, True)
        else:
            # Unix-like systems interrupt handling
            def unix_handler():
                self.interrupt_flag.set()
                self.logger.warning("\nCtrl+C pressed. Cleaning up and writing data...")

            for signame in ('SIGINT', 'SIGTERM'):
                asyncio.get_event_loop().add_signal_handler(
                    getattr(signal, signame),
                    unix_handler)

    def initialize_csv_writer(self):
        if self.csvfile is None:
            self.csvfile = open(self.output_file, 'w', newline='', encoding='utf-8')
            self.csv_writer = csv.writer(self.csvfile)
            self.csv_writer.writerow(CSV_HEADER)

    async def write_csv_block(self) -> None:
        self.logger.info(f"Writing CSV block. Records in block: {len(self.mft_records)}")
        try:
            if self.csv_writer is None:
                self.initialize_csv_writer()
            
            for record in self.mft_records.values():
                try:
                    filepath = self.build_filepath(record)
                    csv_row = record.to_csv()
                    csv_row[-1] = filepath

                    csv_row = [str(item) for item in csv_row]
                    
                    self.csv_writer.writerow(csv_row)
                    if self.debug:
                        self.logger.info(f"Wrote record {record.recordnum} to CSV")
                except Exception as e:
                    self.logger.warning(f"Error writing record {record.recordnum}: {str(e)}")
                    if self.debug:
                        self.logger.debug("Full traceback:", exc_info=True)

            if self.csvfile:
                self.csvfile.flush()
            self.logger.info(f"CSV block written. Current file size: {self.csvfile.tell() if self.csvfile else 0} bytes")
        except Exception as e:
            self.logger.error(f"Error in write_csv_block: {str(e)}")
            if self.debug:
                self.logger.debug("Full traceback:", exc_info=True)


    async def write_remaining_records(self) -> None:
        await self.write_csv_block()
        self.mft_records.clear()

    def build_filepath(self, record: MftRecord) -> str:
        path_parts = []
        current_record = record
        max_depth = 255

        while current_record and max_depth > 0:
            if current_record.recordnum == 5:  
                path_parts.insert(0, "")
                break
            elif current_record.filename:
                path_parts.insert(0, current_record.filename)
            else:
                path_parts.insert(0, f"Unknown_{current_record.recordnum}")

            parent_record_num = current_record.get_parent_record_num()
            
            if parent_record_num == current_record.recordnum:
                path_parts.insert(0, "OrphanedFiles")
                break
            
            current_record = self.mft_records.get(parent_record_num)
            if not current_record:
                path_parts.insert(0, f"UnknownParent_{parent_record_num}")
                break

            max_depth -= 1

        if max_depth == 0:
            path_parts.insert(0, "DeepPath")

        return '\\'.join(path_parts)

    def print_statistics(self) -> None:
        self.logger.warning("\nMFT Analysis Statistics:")
        self.logger.warning(f"Total records processed: {self.stats['total_records']}")
        self.logger.warning(f"Active records: {self.stats['active_records']}")
        self.logger.warning(f"Directories: {self.stats['directories']}")
        self.logger.warning(f"Files: {self.stats['files']}")
        if self.compute_hashes:
            self.logger.warning(f"Unique MD5 hashes: {len(self.stats['unique_md5'])}")
            self.logger.warning(f"Unique SHA256 hashes: {len(self.stats['unique_sha256'])}")
            self.logger.warning(f"Unique SHA512 hashes: {len(self.stats['unique_sha512'])}")
            self.logger.warning(f"Unique CRC32 hashes: {len(self.stats['unique_crc32'])}")


    async def write_output(self) -> None:
        self.logger.warning(f"Writing output in {self.export_format} format to {self.output_file}")
        if self.export_format == "csv":
            await self.write_remaining_records()
        elif self.export_format == "json":
            await FileWriters.write_json(list(self.mft_records.values()), self.output_file)
        elif self.export_format == "xml":
            await FileWriters.write_xml(list(self.mft_records.values()), self.output_file)
        elif self.export_format == "excel":
            await FileWriters.write_excel(list(self.mft_records.values()), self.output_file)
        elif self.export_format == "sqlite":
            await FileWriters.write_sqlite(list(self.mft_records.values()), self.output_file)
        elif self.export_format == "tsk":
            await FileWriters.write_tsk(list(self.mft_records.values()), self.output_file)
        elif self.export_format == "body":
            await FileWriters.write_body(list(self.mft_records.values()), self.output_file)
        elif self.export_format == "timeline":
            await FileWriters.write_timeline(list(self.mft_records.values()), self.output_file)
        else:
            self.logger.error(f"Unsupported export format: {self.export_format}")

    async def cleanup(self):
        self.logger.warning("Performing cleanup...")
         # to-do add more cleanup after database stuff is integrated.
        await self.write_remaining_records()
        self.logger.warning("Cleanup complete.")

    async def create_sqlite_database(self):
        conn = sqlite3.connect(self.output_file)
        cursor = conn.cursor()

        # Create and populate static tables
        sql_dir = os.path.join(os.path.dirname(__file__), 'sql')
        for sql_file in os.listdir(sql_dir):
            with open(os.path.join(sql_dir, sql_file), 'r') as f:
                cursor.executescript(f.read())

        # Create MFT records table
        cursor.execute('''
            CREATE TABLE mft_records (
                record_number INTEGER PRIMARY KEY,
                filename TEXT,
                parent_record_number INTEGER,
                -- Add other fields as needed
                FOREIGN KEY (attribute_type) REFERENCES attribute_types(id)
            )
        ''')

        conn.commit()
        return conn

    async def write_sqlite(self):
        conn = await self.create_sqlite_database()
        cursor = conn.cursor()

        for record in self.mft_records.values():
            cursor.execute('''
                INSERT INTO mft_records (record_number, filename, parent_record_number)
                VALUES (?, ?, ?)
            ''', (record.recordnum, record.filename, record.get_parent_record_num()))

        conn.commit()
        conn.close()
