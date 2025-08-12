import asyncio
import csv
import io
import logging
import os
import signal
import sqlite3
import sys
import traceback
import json
from typing import Dict, Set, List, Optional, Any
from pathlib import Path

from .constants import *
from .mft_record import MftRecord
from .file_writers import FileWriters, get_writer
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
        self.chunk_size = chunk_size
        self.multiprocessing_hashes = multiprocessing_hashes
        self.hash_processes = hash_processes
        
        if profile:
            if not export_format or export_format == "csv":
                self.export_format = profile.export_format
            if not compute_hashes:
                self.compute_hashes = profile.compute_hashes
            if verbosity == 0:
                self.verbosity = profile.verbosity
            if debug == 0:
                self.debug = profile.debug
            if hasattr(profile, 'chunk_size') and chunk_size == 1000:
                self.chunk_size = profile.chunk_size
        
        self.csvfile = None
        self.csv_writer = None
        self.sqlite_writer = None
        self.hash_processor = None
        self.interrupt_flag = asyncio.Event()
        self.logger = logging.getLogger('analyzeMFT.analyzer')
        
        self.setup_logging()
        self.setup_interrupt_handler()
        
        self.mft_records: Dict[int, MftRecord] = {}
        self.current_chunk: List[MftRecord] = []
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
        if self.debug >= 2:
            self.logger.setLevel(logging.DEBUG)
        elif self.debug >= 1 or self.verbosity >= 2:
            self.logger.setLevel(logging.INFO)
        elif self.verbosity >= 1:
            self.logger.setLevel(logging.WARNING)
        else:
            self.logger.setLevel(logging.ERROR)
        
        if self.debug >= 1 and not any(isinstance(h, logging.FileHandler) for h in self.logger.handlers):
            log_file = f"{self.output_file}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def setup_interrupt_handler(self) -> None:
        def interrupt_handler(signum, frame):
            self.logger.warning("Interrupt received. Cleaning up...")
            self.interrupt_flag.set()

        try:
            if sys.platform == "win32":
                import win32api
                win32api.SetConsoleCtrlHandler(lambda x: interrupt_handler(None, None), True)
            else:
                signal.signal(signal.SIGINT, interrupt_handler)
                signal.signal(signal.SIGTERM, interrupt_handler)
        except Exception as e:
            self.logger.warning(f"Could not set up interrupt handler: {e}")

    async def analyze(self) -> None:
        try:
            self.logger.warning("Starting MFT analysis...")
            
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
                try:
                    self.csvfile.close()
                except Exception as e:
                    self.logger.warning(f"Error closing CSV file: {e}")
            
            if self.interrupt_flag.is_set():
                self.logger.warning("Analysis interrupted by user.")
            else:
                self.logger.warning("Analysis complete.")
            
            self.print_statistics()
            
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
                records_processed = 0
                
                while not self.interrupt_flag.is_set():
                    chunk = await self.read_chunk(f)
                    if not chunk:
                        break
                    
                    await self.process_chunk(chunk)
                    
                    if self.current_chunk:
                        await self.write_chunk()
                        self.current_chunk.clear()
                        self.chunk_count += 1
                        self.stats['chunks_processed'] += 1
                    
                    records_processed += len(chunk)
                    
                    if self.interrupt_flag.is_set():
                        self.logger.warning("Interrupt detected. Stopping processing.")
                        break

        except FileNotFoundError:
            self.logger.error(f"MFT file not found: {self.mft_file}")
            raise
        except PermissionError:
            self.logger.error(f"Permission denied accessing MFT file: {self.mft_file}")
            raise
        except Exception as e:
            self.logger.error(f"Error reading MFT file: {str(e)}")
            if self.debug >= 1:
                self.logger.debug("Full traceback:", exc_info=True)
            raise

        self.logger.warning(f"MFT processing complete. Total records processed: {self.stats['total_records']}")
        self.logger.warning(f"Total chunks processed: {self.stats['chunks_processed']}")
        self.logger.warning(f"Total bytes processed: {self.stats['bytes_processed']:,}")

    async def read_chunk(self, file) -> List[bytes]:

        chunk = []
        for _ in range(self.chunk_size):
            if self.interrupt_flag.is_set():
                break
            try:
                raw_record = file.read(MFT_RECORD_SIZE)
                if not raw_record or len(raw_record) < MFT_RECORD_SIZE:
                    break
                chunk.append(raw_record)
                self.stats['bytes_processed'] += MFT_RECORD_SIZE
            except Exception as e:
                self.logger.warning(f"Error reading record: {e}")
                break
        return chunk

    async def process_chunk(self, raw_records: List[bytes]) -> None:

        if self.compute_hashes and self.multiprocessing_hashes and not self.hash_processor:
            self.hash_processor = HashProcessor(
                num_processes=self.hash_processes,
                logger=self.logger
            )
            self.logger.info(f"Initialized HashProcessor with {self.hash_processor.num_processes} processes")
        
        hash_results = []
        if self.compute_hashes and self.multiprocessing_hashes and self.hash_processor:
            self.logger.debug(f"Computing hashes for {len(raw_records)} records using multiprocessing")
            try:
                hash_results = self.hash_processor.compute_hashes_adaptive(raw_records)
            except Exception as e:
                self.logger.error(f"Error computing hashes: {e}")
                hash_results = []
        
        for i, raw_record in enumerate(raw_records):
            if self.interrupt_flag.is_set():
                break
            
            try:
                compute_individual_hashes = self.compute_hashes and not self.multiprocessing_hashes
                record = MftRecord(raw_record, compute_individual_hashes, self.debug, self.logger)
                self.stats['total_records'] += 1
                
                if self.compute_hashes and self.multiprocessing_hashes and i < len(hash_results):
                    try:
                        hash_result = hash_results[i]
                        record.set_hashes(hash_result.md5, hash_result.sha256, hash_result.sha512, hash_result.crc32)
                        
                        if 'unique_md5' in self.stats:
                            self.stats['unique_md5'].add(hash_result.md5)
                            self.stats['unique_sha256'].add(hash_result.sha256)
                            self.stats['unique_sha512'].add(hash_result.sha512)
                            self.stats['unique_crc32'].add(hash_result.crc32)
                    except Exception as e:
                        self.logger.warning(f"Error applying hash results for record {record.recordnum}: {e}")
                
                if record.flags & FILE_RECORD_IN_USE:
                    self.stats['active_records'] += 1
                if record.flags & FILE_RECORD_IS_DIRECTORY:
                    self.stats['directories'] += 1
                else:
                    self.stats['files'] += 1
                
                self.mft_records[record.recordnum] = record
                self.current_chunk.append(record)

                if self.debug >= 2:
                    self.logger.info(f"Processed record {self.stats['total_records']}: {record.filename}")
                elif self.stats['total_records'] % 10000 == 0:
                    self.logger.warning(f"Processed {self.stats['total_records']} records...")

            except Exception as e:
                self.logger.warning(f"Error processing record {self.stats['total_records']}: {str(e)}")
                if self.debug >= 2:
                    self.logger.debug("Full traceback:", exc_info=True)
                continue

    def initialize_csv_writer(self) -> None:
        if self.csvfile is None:
            try:
                self.csvfile = open(self.output_file, 'w', newline='', encoding='utf-8')
                self.csv_writer = csv.writer(self.csvfile)
                self.csv_writer.writerow(CSV_HEADER)
            except Exception as e:
                self.logger.error(f"Error initializing CSV writer: {e}")
                raise

    async def write_chunk(self) -> None:
        self.logger.info(f"Writing chunk {self.chunk_count + 1}. Records in chunk: {len(self.current_chunk)}")
        try:
            if self.export_format == "csv":
                await self.write_csv_chunk()
            elif self.export_format == "json":
                await self.write_json_chunk()
            elif self.export_format == "sqlite":
                await self.write_sqlite_chunk()
            else:
                await self.write_csv_chunk()
            
            self.logger.info(f"Chunk {self.chunk_count + 1} written successfully")
        except Exception as e:
            self.logger.error(f"Error writing chunk {self.chunk_count + 1}: {str(e)}")
            if self.debug:
                self.logger.debug("Full traceback:", exc_info=True)

    async def write_csv_chunk(self) -> None:
        if self.csv_writer is None:
            self.initialize_csv_writer()
        
        try:
            for record in self.current_chunk:
                try:
                    filepath = self.build_filepath(record)
                    csv_row = record.to_csv()
                    csv_row[8] = filepath 
                    
                    csv_row = [str(item) for item in csv_row]
                    
                    self.csv_writer.writerow(csv_row)
                    
                    if self.debug >= 3:
                        self.logger.debug(f"Wrote record {record.recordnum} to CSV")
                except Exception as e:
                    self.logger.warning(f"Error writing record {record.recordnum}: {str(e)}")
                    if self.debug >= 2:
                        self.logger.debug("Full traceback:", exc_info=True)

            if self.csvfile:
                self.csvfile.flush()
        except Exception as e:
            self.logger.error(f"Error in write_csv_chunk: {e}")
            raise

    async def write_json_chunk(self) -> None:
        try:
            chunk_filename = f"{self.output_file}.chunk_{self.chunk_count + 1}.json"
            chunk_data = []
            
            for record in self.current_chunk:
                try:
                    filepath = self.build_filepath(record)
                    record_dict = {
                        'recordnum': record.recordnum,
                        'filename': record.filename,
                        'filepath': filepath,
                        'filesize': record.filesize,
                        'flags': record.flags,
                        'parent_ref': record.get_parent_record_num(),
                        'si_times': {k: v.dtstr for k, v in record.si_times.items()},
                        'fn_times': {k: v.dtstr for k, v in record.fn_times.items()},
                        'attribute_types': list(record.attribute_types),
                        'md5': getattr(record, 'md5', None),
                        'sha256': getattr(record, 'sha256', None),
                        'sha512': getattr(record, 'sha512', None),
                        'crc32': getattr(record, 'crc32', None)
                    }
                    chunk_data.append(record_dict)
                except Exception as e:
                    self.logger.warning(f"Error processing record {record.recordnum} for JSON: {e}")
            
            with open(chunk_filename, 'w', encoding='utf-8') as f:
                json.dump(chunk_data, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Error writing JSON chunk: {e}")
            raise

    async def write_sqlite_chunk(self) -> None:
        if self.sqlite_writer is None:
            try:
                self.sqlite_writer = SQLiteWriter(self.output_file, self.logger)
                self.sqlite_writer.connect()
            except Exception as e:
                self.logger.error(f"Error initializing SQLite writer: {e}")
                raise
        
        try:
            filepaths = {}
            for record in self.current_chunk:
                try:
                    filepaths[record.recordnum] = self.build_filepath(record)
                except Exception as e:
                    self.logger.warning(f"Error building filepath for record {record.recordnum}: {e}")
                    filepaths[record.recordnum] = f"UnknownPath_{record.recordnum}"
            
            self.sqlite_writer.write_records_batch(self.current_chunk, filepaths)
            self.logger.info(f"Successfully wrote {len(self.current_chunk)} records to SQLite")
            
        except Exception as e:
            self.logger.error(f"Error writing SQLite chunk: {e}")
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
        self.logger.warning(f"Bytes processed: {self.stats['bytes_processed']:,}")
        self.logger.warning(f"Chunks processed: {self.stats['chunks_processed']}")
        
        if self.compute_hashes:
            self.logger.warning(f"Unique MD5 hashes: {len(self.stats['unique_md5'])}")
            self.logger.warning(f"Unique SHA256 hashes: {len(self.stats['unique_sha256'])}")
            self.logger.warning(f"Unique SHA512 hashes: {len(self.stats['unique_sha512'])}")
            self.logger.warning(f"Unique CRC32 hashes: {len(self.stats['unique_crc32'])}")

    async def write_output(self) -> None:
        self.logger.warning(f"Writing output in {self.export_format} format to {self.output_file}")
        
        try:
            writer_func = get_writer(self.export_format)
            
            if writer_func:
                await writer_func(list(self.mft_records.values()), self.output_file)
            else:
                self.logger.warning(f"Unsupported export format '{self.export_format}', falling back to CSV")
                await FileWriters.write_csv(list(self.mft_records.values()), self.output_file)
                
        except Exception as e:
            self.logger.error(f"Error writing output: {e}")
            if self.debug:
                self.logger.debug("Full traceback:", exc_info=True)
            raise

    async def create_sqlite_database(self) -> sqlite3.Connection:

        try:
            conn = sqlite3.connect(self.output_file)
            cursor = conn.cursor()
            
            sql_dir = Path(__file__).parent / 'sql'
            if sql_dir.exists():
                for sql_file in sql_dir.glob('*.sql'):
                    try:
                        with open(sql_file, 'r') as f:
                            cursor.executescript(f.read())
                    except Exception as e:
                        self.logger.warning(f"Error executing SQL script {sql_file}: {e}")
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mft_records (
                    record_number INTEGER PRIMARY KEY,
                    filename TEXT,
                    parent_record_number INTEGER,
                    file_size INTEGER,
                    is_directory INTEGER,
                    creation_time TEXT,
                    modification_time TEXT,
                    access_time TEXT,
                    entry_time TEXT,
                    attribute_types TEXT
                )
            ''')

            conn.commit()
            return conn
            
        except Exception as e:
            self.logger.error(f"Error creating SQLite database: {e}")
            raise

    async def write_sqlite(self) -> None:
        try:
            conn = await self.create_sqlite_database()
            cursor = conn.cursor()

            for record in self.mft_records.values():
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO mft_records (
                            record_number, filename, parent_record_number, file_size,
                            is_directory, creation_time, modification_time, access_time,
                            entry_time, attribute_types
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        record.recordnum,
                        record.filename,
                        record.get_parent_record_num(),
                        record.filesize,
                        1 if record.flags & FILE_RECORD_IS_DIRECTORY else 0,
                        record.fn_times['crtime'].dtstr,
                        record.fn_times['mtime'].dtstr,
                        record.fn_times['atime'].dtstr,
                        record.fn_times['ctime'].dtstr,
                        ','.join(map(str, record.attribute_types))
                    ))
                except Exception as e:
                    self.logger.warning(f"Error inserting record {record.recordnum}: {e}")

            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error writing to SQLite: {e}")
            raise