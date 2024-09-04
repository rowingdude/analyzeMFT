import asyncio
import csv
import io
import sys
import traceback
from typing import Dict, Set, List, Optional, Any
from .constants import *
from .mft_record import MftRecord
from .file_writers import FileWriters

class MftAnalyzer:

    def __init__(self, mft_file: str, output_file: str, debug: bool = False, very_debug: bool = False, 
                 verbosity: int = 0, compute_hashes: bool = False, export_format: str = "csv") -> None:
        self.mft_file = mft_file
        self.output_file = output_file
        self.debug = debug
        self.very_debug = very_debug
        self.verbosity = verbosity
        self.compute_hashes = compute_hashes
        self.export_format = export_format
        self.compute_hashes = compute_hashes
        self.export_format = export_format
        self.mft_records = {}  
        self.interrupt_flag = asyncio.Event()
        
        self.csvfile = None
        self.csv_writer = None

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

    def log(self, message: str, level: int = 0):
        if level <= self.debug or level <= self.verbosity:
            print(message)

    async def analyze(self) -> None:
        try:
            self.initialize_csv_writer()
            await self.process_mft()
            await self.write_output()
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            if self.debug:
                traceback.print_exc()
        finally:
            if self.csvfile:
                self.csvfile.close()
            self.print_statistics()


    async def process_mft(self) -> None:
        self.log(f"Processing MFT file: {self.mft_file}", 1)
        try:
            with open(self.mft_file, 'rb') as f:
                while not self.interrupt_flag.is_set():
                    raw_record = f.read(MFT_RECORD_SIZE)
                    if not raw_record:
                        break

                    try:
                        record = MftRecord(raw_record, self.compute_hashes)
                        self.stats['total_records'] += 1
                        
                        if record.flags & FILE_RECORD_IN_USE:
                            self.stats['active_records'] += 1
                        if record.flags & FILE_RECORD_IS_DIRECTORY:
                            self.stats['directories'] += 1
                        else:
                            self.stats['files'] += 1

                        self.mft_records[record.recordnum] = record

                        if self.debug >= 2:
                            self.log(f"Processed record {self.stats['total_records']}: {record.filename}", 2)
                        elif self.stats['total_records'] % 10000 == 0:
                            self.log(f"Processed {self.stats['total_records']} records...", 1)

                        if self.stats['total_records'] % 1000 == 0:
                            await self.write_csv_block()
                            self.mft_records.clear()

                    except Exception as e:
                        self.log(f"Error processing record {self.stats['total_records']}: {str(e)}", 1)
                        if self.debug >= 2:
                            traceback.print_exc()
                        continue

        except Exception as e:
            self.log(f"Error reading MFT file: {str(e)}", 0)
            if self.debug >= 1:
                traceback.print_exc()

        self.log(f"MFT processing complete. Total records processed: {self.stats['total_records']}", 0)


    def handle_interrupt(self) -> None:
        if sys.platform == "win32":
            # Windows-specific interrupt handling
            import win32api
            def windows_handler(type):
                self.interrupt_flag.set()
                print("\nCtrl+C pressed. Cleaning up and writing data...")
                return True
            win32api.SetConsoleCtrlHandler(windows_handler, True)
        else:
            # Unix-like systems interrupt handling
            def unix_handler():
                self.interrupt_flag.set()
                print("\nCtrl+C pressed. Cleaning up and writing data...")

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
        self.log(f"Writing CSV block. Records in block: {len(self.mft_records)}", 2)
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
                    if self.very_debug:
                        self.log(f"Wrote record {record.recordnum} to CSV", 2)
                except Exception as e:
                    self.log(f"Error writing record {record.recordnum}: {str(e)}", 1)
                    if self.very_debug:
                        traceback.print_exc()

            if self.csvfile:
                self.csvfile.flush()
            self.log(f"CSV block written. Current file size: {self.csvfile.tell() if self.csvfile else 0} bytes", 2)
        except Exception as e:
            self.log(f"Error in write_csv_block: {str(e)}", 0)
            if self.debug or self.very_debug:
                traceback.print_exc()


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
        print("\nMFT Analysis Statistics:")
        print(f"Total records processed: {self.stats['total_records']}")
        print(f"Active records: {self.stats['active_records']}")
        print(f"Directories: {self.stats['directories']}")
        print(f"Files: {self.stats['files']}")
        if self.compute_hashes:
            print(f"Unique MD5 hashes: {len(self.stats['unique_md5'])}")
            print(f"Unique SHA256 hashes: {len(self.stats['unique_sha256'])}")
            print(f"Unique SHA512 hashes: {len(self.stats['unique_sha512'])}")
            print(f"Unique CRC32 hashes: {len(self.stats['unique_crc32'])}")


    async def write_output(self) -> None:
        print(f"Writing output in {self.export_format} format to {self.output_file}")
        if self.export_format == "csv":
            await self.write_remaining_records()
        elif self.export_format == "json":
            await FileWriters.write_json(list(self.mft_records.values()), self.output_file)
        elif self.export_format == "xml":
            await FileWriters.write_xml(list(self.mft_records.values()), self.output_file)
        elif self.export_format == "excel":
            await FileWriters.write_excel(list(self.mft_records.values()), self.output_file)
        else:
            print(f"Unsupported export format: {self.export_format}")