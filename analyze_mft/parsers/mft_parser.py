import concurrent.futures
import logging
from collections import deque
from functools import lru_cache
from typing import List, Dict, Any, Optional, Iterable
from dataclasses import dataclass
import uuid

from .mft_record import MFTRecord
from .logger import Logger
from .json_writer import JSONWriter
from .thread_manager import ThreadManager
from .csv_writer import CSVWriter
from .file_handler import FileHandler
from .windows_time import WindowsTime

@dataclass
class ParserOptions:
    output: Optional[str]
    csvtimefile: Optional[str]
    bodyfile: Optional[str]
    jsonfile: Optional[str]
    thread_count: int

class MFTParser:
    def __init__(self, options: ParserOptions, file_handler: FileHandler, csv_writer: CSVWriter, json_writer: JSONWriter, thread_manager: ThreadManager):
        self.options = options
        self.file_handler = file_handler
        self.csv_writer = csv_writer
        self.json_writer = json_writer
        self.thread_manager = thread_manager
        self.logger = logging.getLogger('analyzeMFT')
        self.mft: Dict[int, Dict[str, Any]] = {}
        self.folders: Dict[int, str] = {}
        self.record_queue = deque(maxlen=10000)
        self.num_records = 0
        self.progress_callback = None

    async def parse_mft_file(self, progress_callback=None):
        self.logger.info("Starting to parse MFT file...")
        self.progress_callback = progress_callback

        if self.options.output is not None:
            await self.csv_writer.write_csv_header()

        raw_records = await self._read_all_records()
        self.logger.info(f"Read {len(raw_records)} raw records from MFT file.")

        await self._process_records(raw_records)

        if progress_callback:
            progress_callback(self.num_records)

        self.logger.info(f"Finished parsing MFT file. Total records: {self.num_records}")

    async def _read_all_records(self) -> List[bytes]:
        return [record async for record in self.file_handler.read_mft_records()]

    async def _process_records(self, raw_records: List[bytes]):
        async with self.thread_manager.executor() as executor:
            futures = [executor.submit(self._parse_single_record, raw_record) for raw_record in raw_records]
            for future in concurrent.futures.as_completed(futures):
                record = await future
                if record:
                    self.record_queue.append(record)
                    if len(self.record_queue) == self.record_queue.maxlen:
                        await self._process_record_queue()

        await self._process_record_queue()  # Process any remaining records

    async def _parse_single_record(self, raw_record: bytes) -> Optional[Dict[str, Any]]:
        try:
            mft_record = MFTRecord(raw_record, self.options)
            record = await mft_record.parse()

            if record is not None:
                await self._parse_object_id(record)
                await self._check_usec_zero(record)
                await self._log_parsed_record(record)
                self.logger.debug(f"Parsed record {record['recordnum']}: filename={record.get('filename', 'N/A')}")
            else:
                self.logger.warning("MFTRecord.parse() returned None")
            return record

        except Exception as e:
            self.logger.error(f"Error parsing record: {str(e)}")
            return None

    async def _process_record_queue(self):
        while self.record_queue:
            record = self.record_queue.popleft()
            self.mft[self.num_records] = record
            self.num_records += 1
            if self.num_records % 1000 == 0:
                self.logger.info(f"Parsed {self.num_records} records...")
                if self.progress_callback:
                    self.progress_callback(self.num_records)

    async def _parse_object_id(self, record: Dict[str, Any]):
        if 'objid' in record:
            objid_data = record['objid']
            
            if len(objid_data) >= 16:
                record['object_id'] = str(uuid.UUID(bytes_le=objid_data[:16]))

                if len(objid_data) >= 32:
                    record['birth_volume_id'] = str(uuid.UUID(bytes_le=objid_data[16:32]))

                    if len(objid_data) >= 48:
                        record['birth_object_id'] = str(uuid.UUID(bytes_le=objid_data[32:48]))

                        if len(objid_data) >= 64:
                            record['birth_domain_id'] = str(uuid.UUID(bytes_le=objid_data[48:64]))
            
            self.logger.debug(f"Parsed Object ID for record {record['recordnum']}: "
                              f"Object ID: {record.get('object_id', 'N/A')}, "
                              f"Birth Volume ID: {record.get('birth_volume_id', 'N/A')}, "
                              f"Birth Object ID: {record.get('birth_object_id', 'N/A')}, "
                              f"Birth Domain ID: {record.get('birth_domain_id', 'N/A')}")

    async def _check_usec_zero(self, record: Dict[str, Any]):
        if 'si' in record:
            si_times = [record['si'][key] for key in ['crtime', 'mtime', 'atime', 'ctime']]
            record['usec-zero'] = all(isinstance(time, WindowsTime) and time.unixtime % 1 == 0 for time in si_times)
            self.logger.debug(f"Record {record['recordnum']} usec-zero: {record['usec-zero']}")

    async def generate_filepaths(self):
        self.logger.info("Generating file paths...")
        for i in self.mft:
            if self.mft[i]['filename'] == '':
                if self.mft[i]['fncnt'] > 0:
                    await self.get_folder_path(i)
                else:
                    self.mft[i]['filename'] = 'NoFNRecord'
        self.logger.info("Finished generating file paths.")

    @lru_cache(maxsize=1000)
    async def get_folder_path(self, seqnum: int, visited: Optional[set] = None) -> str:
        if visited is None:
            visited = set()
        
        if seqnum in visited:
            return 'Circular_Reference'
        
        visited.add(seqnum)
        
        if seqnum not in self.mft:
            return 'Orphan'

        if self.mft[seqnum]['filename'] != '':
            return self.mft[seqnum]['filename']

        try:
            if self.mft[seqnum]['fn', 0]['par_ref'] == 5:
                self.mft[seqnum]['filename'] = '/' + self.mft[seqnum]['fn', self.mft[seqnum]['fncnt'] - 1]['name']
                return self.mft[seqnum]['filename']
        except KeyError:
            self.mft[seqnum]['filename'] = 'NoFNRecord'
            return self.mft[seqnum]['filename']

        if self.mft[seqnum]['fn', 0]['par_ref'] == seqnum:
            self.mft[seqnum]['filename'] = f"ORPHAN/{self.mft[seqnum]['fn', self.mft[seqnum]['fncnt'] - 1]['name']}"
            return self.mft[seqnum]['filename']

        parentpath = await self.get_folder_path(self.mft[seqnum]['fn', 0]['par_ref'], visited)
        self.mft[seqnum]['filename'] = f"{parentpath}/{self.mft[seqnum]['fn', self.mft[seqnum]['fncnt'] - 1]['name']}"

        return self.mft[seqnum]['filename']

    async def print_records(self):
        self.logger.info("Writing records to output files...")
        for i in self.mft:
            if self.options.output is not None:
                await self.csv_writer.write_csv_record(self.mft[i])
            if self.options.csvtimefile is not None:
                await self.csv_writer.write_l2t(self.mft[i])
            if self.options.bodyfile is not None:
                await self.csv_writer.write_bodyfile(self.mft[i])
            if self.options.jsonfile is not None:
                await self.json_writer.write_json_record(self.mft[i])

        if self.options.jsonfile is not None:
            await self.json_writer.write_json_file()
        
        self.logger.info("Finished writing records to output files.")

    async def _log_parsed_record(self, record: Dict[str, Any]):
        self.logger.debug(f"Parsed record {record['recordnum']}:")
        self.logger.debug(f"Filename: {record.get('filename', 'N/A')}")
        if 'si' in record:
            self.logger.debug("Standard Information timestamps:")
            for key in ['crtime', 'mtime', 'atime', 'ctime']:
                self.logger.debug(f"  {key.capitalize()} time: {record['si'][key]}")

    def get_total_records(self) -> int:
        return self.file_handler.estimate_total_records()

    @error_handler
    async def parse_mft(mft_parser: MFTParser, progress_callback: Callable[[int], None]) -> None:
        await mft_parser.parse_mft_file(progress_callback)
        await mft_parser.generate_filepaths()
        await mft_parser.print_records()