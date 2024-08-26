import concurrent.futures
import logging
from collections import deque
from functools import lru_cache
from typing import List, Dict, Any, Optional, Callable, Iterable
from dataclasses import dataclass
import traceback
import uuid

from analyze_mft.utilities.mft_record import MFTRecord
from analyze_mft.utilities.logger import Logger
from analyze_mft.outputs.json_writer import JSONWriter
from analyze_mft.utilities.thread_manager import ThreadManager
from analyze_mft.outputs.csv_writer import CSVWriter
from analyze_mft.utilities.file_handler import FileHandler
from analyze_mft.utilities.windows_time import WindowsTime
from analyze_mft.utilities.error_handler import error_handler

@error_handler
async def parse_mft(mft_parser: MFTParser) -> None:
    print("Starting parse_mft function")
    try:
        await mft_parser.parse_mft_file()
        print("Finished parsing MFT file")
        await mft_parser.generate_filepaths()
        print("Finished generating filepaths")
        await mft_parser.print_records()
        print("Finished printing records")
    except Exception as e:
        print(f"Error in parse_mft: {str(e)}")
        traceback.print_exc()

@dataclass
class ParserOptions:
    output: Optional[str]
    csvtimefile: Optional[str]
    bodyfile: Optional[str]
    jsonfile: Optional[str]
    thread_count: int

class MFTParser:
    def __init__(self, options, file_handler, csv_writer, json_writer, thread_manager):
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
        

    async def parse_mft_file(self):
        print("Starting to parse MFT file...")
        self.logger.info("Starting to parse MFT file...")

        try:
            if self.options.output is not None:
                print("Writing CSV header...")
                await self.csv_writer.write_csv_header()
                print("CSV header written")

            print("Reading raw records...")
            raw_records = await self._read_all_records()
            print(f"Read {len(raw_records)} raw records from MFT file.")
            self.logger.info(f"Read {len(raw_records)} raw records from MFT file.")

            if not raw_records:
                print("No records read from MFT file. Exiting.")
                return

            print("Processing records...")
            await self._process_records(raw_records)

            print(f"Finished parsing MFT file. Total records: {self.num_records}")
            self.logger.info(f"Finished parsing MFT file. Total records: {self.num_records}")
        except Exception as e:
            print(f"Error in parse_mft_file: {str(e)}")
            traceback.print_exc()

    async def _read_all_records(self) -> List[bytes]:
        records = []
        try:
            while True:
                record = await self.file_handler.read_mft_record()
                if not record:
                    break
                records.append(record)
                if len(records) % 10000 == 0:
                    print(f"Read {len(records)} records so far...")
            return records
        except Exception as e:
            print(f"Error in _read_all_records: {str(e)}")
            traceback.print_exc()
            return []

    async def _process_records(self, raw_records: List[bytes]):
        print(f"Processing {len(raw_records)} records")
        try:
            for i, raw_record in enumerate(raw_records):
                record = await self._parse_single_record(raw_record)
                if record:
                    self.record_queue.append(record)
                    if len(self.record_queue) == self.record_queue.maxlen:
                        await self._process_record_queue()
                if i % 10000 == 0:
                    print(f"Processed {i} records")
            await self._process_record_queue()  # Process any remaining records
            print("Finished processing all records")
        except Exception as e:
            print(f"Error in _process_records: {str(e)}")
            traceback.print_exc()

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
        print(f"Processing record queue with {len(self.record_queue)} records")
        while self.record_queue:
            record = self.record_queue.popleft()
            self.mft[self.num_records] = record
            
            if self.options.output is not None:
                print(f"Writing record {record['recordnum']} to CSV")
                await self.csv_writer.write_csv_record(record)
            
            self.num_records += 1
            if self.num_records % 1000 == 0:
                print(f"Processed {self.num_records} records")
                self.logger.info(f"Parsed {self.num_records} records...")
        print("Finished processing record queue")


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

