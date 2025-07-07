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
from .config import AnalysisProfile
from .sqlite_writer import SQLiteWriter
from .hash_processor import HashProcessor

class MftAnalyzer:
    def __init__(self, mft_file: str, output_file: str, debug: int = 0, verbosity: int = 0, 
                 compute_hashes: bool = False, export_format: str = "csv", 
                 profile: Optional[AnalysisProfile] = None, chunk_size: int = 1000,
                 multiprocessing_hashes: bool = True, hash_processes: Optional[int] = None) -> None:
        self.mft_file = mft_file
        self.output_file = output_file
        self.debug = debug
        self.verbosity = int(verbosity) 
        self.compute_hashes = compute_hashes
        self.export_format = export_format
        self.profile = profile
        self.chunk_size = chunk_size  # Number of records to process before writing
        self.multiprocessing_hashes = multiprocessing_hashes
        self.hash_processes = hash_processes
        
        # Apply profile settings if provided
        if profile:
            # Use profile settings as defaults, CLI args take precedence
            if not export_format or export_format == "csv":
                self.export_format = profile.export_format
            if not compute_hashes:
                self.compute_hashes = profile.compute_hashes
            if verbosity == 0:
                self.verbosity = profile.verbosity
            if debug == 0:
                self.debug = profile.debug
            # Apply chunk_size from profile if available
            if hasattr(profile, 'chunk_size') and chunk_size == 1000:
                self.chunk_size = profile.chunk_size
        
        self.csvfile = None
        self.csv_writer = None
        self.sqlite_writer = None
        self.hash_processor = None
        self.interrupt_flag = asyncio.Event()
        self.setup_logging()
        self.setup_interrupt_handler()
        
        self.mft_records = {}
        self.current_chunk = []  # Current chunk being processed
        self.chunk_count = 0
        self.stats = {
            'total_records': 0,
            'active_records': 0,
            'directories': 0,
            'files': 0,
            'bytes_processed': 0,
            'chunks_processed': 0,
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
            # Only initialize CSV writer if export format is CSV
            if self.export_format == "csv":
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
            # Don't close SQLite writer here - it will be closed in write_output
            if self.interrupt_flag.is_set():
                self.logger.warning("Analysis interrupted by user.")
            else:
                self.logger.warning("Analysis complete.")
            self.print_statistics()
            
            # Close SQLite writer after everything is done
            if self.sqlite_writer:
                try:
                    self.sqlite_writer.close()
                    self.logger.info("Final SQLite database cleanup completed")
                except Exception as e:
                    self.logger.warning(f"Error during final SQLite cleanup: {e}")


    async def process_mft(self) -> None:
        self.logger.warning(f"Processing MFT file: {self.mft_file}")
        self.logger.warning(f"Using chunk size: {self.chunk_size} records")
        
        try:
            file_size = os.path.getsize(self.mft_file)
            estimated_records = file_size // MFT_RECORD_SIZE
            self.logger.warning(f"MFT file size: {file_size:,} bytes, estimated {estimated_records:,} records")
            
            with open(self.mft_file, 'rb') as f:
                while not self.interrupt_flag.is_set():
                    # Process chunk of records
                    chunk = await self.read_chunk(f)
                    if not chunk:
                        break
                    
                    await self.process_chunk(chunk)
                    
                    # Write chunk to output and clear memory
                    if self.current_chunk:
                        await self.write_chunk()
                        self.current_chunk.clear()
                        self.chunk_count += 1
                        self.stats['chunks_processed'] += 1
                    
                    if self.interrupt_flag.is_set():
                        self.logger.warning("Interrupt detected. Stopping processing.")
                        break

        except Exception as e:
            self.logger.error(f"Error reading MFT file: {str(e)}")
            if self.debug >= 1:
                self.logger.debug("Full traceback:", exc_info=True)

        self.logger.warning(f"MFT processing complete. Total records processed: {self.stats['total_records']}")
        self.logger.warning(f"Total chunks processed: {self.stats['chunks_processed']}")
        self.logger.warning(f"Total bytes processed: {self.stats['bytes_processed']:,}")

    async def read_chunk(self, file) -> List[bytes]:
        """Read a chunk of raw MFT records from file."""
        chunk = []
        for _ in range(self.chunk_size):
            if self.interrupt_flag.is_set():
                break
            raw_record = file.read(MFT_RECORD_SIZE)
            if not raw_record or len(raw_record) < MFT_RECORD_SIZE:
                break
            chunk.append(raw_record)
            self.stats['bytes_processed'] += MFT_RECORD_SIZE
        return chunk

    async def process_chunk(self, raw_records: List[bytes]) -> None:
        """Process a chunk of raw MFT records."""
        # Initialize hash processor if needed
        if self.compute_hashes and self.multiprocessing_hashes and self.hash_processor is None:
            self.hash_processor = HashProcessor(
                num_processes=self.hash_processes,
                logger=self.logger
            )
            self.logger.info(f"Initialized HashProcessor with {self.hash_processor.num_processes} processes")
        
        # Compute hashes for all records in batch if using multiprocessing
        hash_results = []
        if self.compute_hashes and self.multiprocessing_hashes and self.hash_processor:
            self.logger.debug(f"Computing hashes for {len(raw_records)} records using multiprocessing")
            hash_results = self.hash_processor.compute_hashes_adaptive(raw_records)
        
        for i, raw_record in enumerate(raw_records):
            if self.interrupt_flag.is_set():
                break
            
            try:
                # Create record without computing hashes if using multiprocessing
                compute_individual_hashes = self.compute_hashes and not self.multiprocessing_hashes
                record = MftRecord(raw_record, compute_individual_hashes, self.debug, self.logger)
                self.stats['total_records'] += 1
                
                # Apply pre-computed hashes if using multiprocessing
                if self.compute_hashes and self.multiprocessing_hashes and i < len(hash_results):
                    hash_result = hash_results[i]
                    record.set_hashes(hash_result.md5, hash_result.sha256, hash_result.sha512, hash_result.crc32)
                    
                    # Update statistics with unique hashes
                    if 'unique_md5' in self.stats:
                        self.stats['unique_md5'].add(hash_result.md5)
                        self.stats['unique_sha256'].add(hash_result.sha256)
                        self.stats['unique_sha512'].add(hash_result.sha512)
                        self.stats['unique_crc32'].add(hash_result.crc32)
                
                if record.flags & FILE_RECORD_IN_USE:
                    self.stats['active_records'] += 1
                if record.flags & FILE_RECORD_IS_DIRECTORY:
                    self.stats['directories'] += 1
                else:
                    self.stats['files'] += 1

                # Store record temporarily for filepath building
                self.mft_records[record.recordnum] = record
                self.current_chunk.append(record)

                if self.debug >= 2:
                    self.logger.info(f"Processed record {self.stats['total_records']}: {record.filename}")
                elif self.stats['total_records'] % 10000 == 0:
                    self.logger.warning(f"Processed {self.stats['total_records']} records...")

            except Exception as e:
                self.logger.warning(f"Error processing record {self.stats['total_records']}: {str(e)}")
                self.logger.info(f"Raw record (first 100 bytes): {raw_record[:100].hex()}")
                if self.debug >= 2:
                    self.logger.debug("Full traceback:", exc_info=True)
                continue

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

    async def write_chunk(self) -> None:
        """Write current chunk of records to output."""
        self.logger.info(f"Writing chunk {self.chunk_count + 1}. Records in chunk: {len(self.current_chunk)}")
        try:
            if self.export_format == "csv":
                await self.write_csv_chunk()
            elif self.export_format == "json":
                await self.write_json_chunk()
            elif self.export_format == "sqlite":
                await self.write_sqlite_chunk()
            else:
                # For other formats, fall back to batch processing
                await self.write_csv_chunk()
            
            self.logger.info(f"Chunk {self.chunk_count + 1} written successfully")
        except Exception as e:
            self.logger.error(f"Error writing chunk {self.chunk_count + 1}: {str(e)}")
            if self.debug:
                self.logger.debug("Full traceback:", exc_info=True)

    async def write_csv_chunk(self) -> None:
        """Write current chunk to CSV format."""
        if self.csv_writer is None:
            self.initialize_csv_writer()
        
        for record in self.current_chunk:
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

    async def write_json_chunk(self) -> None:
        """Write current chunk to JSON format (streaming)."""
        # For streaming JSON, we need to handle chunks differently
        # This is a simplified implementation
        import json
        
        chunk_filename = f"{self.output_file}.chunk_{self.chunk_count + 1}.json"
        with open(chunk_filename, 'w') as f:
            chunk_data = []
            for record in self.current_chunk:
                filepath = self.build_filepath(record)
                record_dict = record.to_dict()
                record_dict['filepath'] = filepath
                chunk_data.append(record_dict)
            json.dump(chunk_data, f, indent=2)

    async def write_sqlite_chunk(self) -> None:
        """Write current chunk to SQLite database."""
        if self.sqlite_writer is None:
            self.sqlite_writer = SQLiteWriter(self.output_file, self.logger)
            self.sqlite_writer.connect()
        
        try:
            # Build filepaths for records
            filepaths = {}
            for record in self.current_chunk:
                try:
                    filepaths[record.recordnum] = self.build_filepath(record)
                except Exception as e:
                    self.logger.warning(f"Error building filepath for record {record.recordnum}: {e}")
                    filepaths[record.recordnum] = f"UnknownPath_{record.recordnum}"
            
            # Write batch to SQLite
            self.sqlite_writer.write_records_batch(self.current_chunk, filepaths)
            self.logger.info(f"Successfully wrote {len(self.current_chunk)} records to SQLite")
            
        except Exception as e:
            self.logger.error(f"Error writing SQLite chunk: {e}")
            if self.debug:
                self.logger.debug("Full traceback:", exc_info=True)
            raise

    async def write_csv_block(self) -> None:
        """Legacy method for compatibility."""
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

    async def write_remaining_sqlite_records(self) -> None:
        """Write any remaining records to SQLite database"""
        try:
            if self.mft_records:
                # Add remaining records to current chunk and write
                for record in self.mft_records.values():
                    self.current_chunk.append(record)
                
                if self.current_chunk:
                    await self.write_sqlite_chunk()
                    self.current_chunk.clear()
                
                self.mft_records.clear()
                self.logger.info("All remaining records written to SQLite database")
                
        except Exception as e:
            self.logger.error(f"Error writing remaining SQLite records: {e}")
            if self.debug:
                self.logger.debug("Full traceback:", exc_info=True)
            raise

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
        elif self.export_format == "sqlite":
            await self.write_remaining_sqlite_records()
        elif self.export_format == "json":
            await FileWriters.write_json(list(self.mft_records.values()), self.output_file)
        elif self.export_format == "xml":
            await FileWriters.write_xml(list(self.mft_records.values()), self.output_file)
        elif self.export_format == "excel":
            await FileWriters.write_excel(list(self.mft_records.values()), self.output_file)
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
