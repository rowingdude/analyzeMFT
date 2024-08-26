import concurrent.futures
import logging
from collections import deque
from functools import lru_cache
from typing import List, Dict, Any, Optional, Callable, Iterable
from dataclasses import dataclass
import traceback
import uuid
import struct

from analyze_mft.utilities.mft_record import MFTRecord
from analyze_mft.utilities.logger import Logger
from analyze_mft.outputs.json_writer import JSONWriter
from analyze_mft.utilities.thread_manager import ThreadManager
from analyze_mft.outputs.csv_writer import CSVWriter
from analyze_mft.utilities.file_handler import FileHandler
from analyze_mft.parsers.attribute_parser import AttributeParser
from analyze_mft.utilities.windows_time import WindowsTime
from analyze_mft.utilities.error_handler import error_handler


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
        self.attribute_parser = AttributeParser
        

    async def parse_mft_file(self):
        if self.options.output:
            await self.csv_writer.write_csv_header()

        while True:
            raw_record = await self.file_handler.read_mft_record()
            if not raw_record:
                break
            record = await self._parse_single_record(raw_record)
            if record:
                self.mft[self.num_records] = record
                if self.options.output:
                    await self.csv_writer.write_csv_record(record)
                if self.options.jsonfile:
                    await self.json_writer.write_json_record(record)
                self.num_records += 1
                self._update_progress()

        print(f"\nTotal records processed: {self.num_records}")
        await self.generate_filepaths()

    if self.num_records % 1000 == 0:
        sys.stdout.write(f"\rProcessed {self.num_records} thousand records")
        sys.stdout.flush()

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
            await self._process_record_queue()  
            print("Finished processing all records")
        except Exception as e:
            print(f"Error in _process_records: {str(e)}")
            traceback.print_exc()

        async def _parse_single_record(self, raw_record: bytes) -> Optional[Dict[str, Any]]:
            record = {}
            record['filename'] = ''
            record['notes'] = ''
            
            self._decode_mft_header(record, raw_record)

            if record['magic'] == 0x44414142:
                record['baad'] = True
                return record

            if record['magic'] != 0x454c4946:
                record['corrupt'] = True
                return record

            # Parse attributes
            offset = record['attr_off']
            while offset < 1024:
                try:
                    attr_header = self.attribute_parser.parse_attribute_header(raw_record[offset:])
                    if attr_header['type'] == 0xffffffff:
                        break
                    await self._parse_attribute(record, raw_record[offset:], attr_header)
                    offset += attr_header['len']
                except Exception as e:
                    record['notes'] += f"Error parsing attribute at offset {offset}: {str(e)} | "
                    break

            return record

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

    def _decode_mft_header(self, record: Dict[str, Any], raw_record: bytes):
        record['magic'] = struct.unpack("<I", raw_record[:4])[0]
        record['upd_off'] = struct.unpack("<H", raw_record[4:6])[0]
        record['upd_cnt'] = struct.unpack("<H", raw_record[6:8])[0]
        record['lsn'] = struct.unpack("<d", raw_record[8:16])[0]
        record['seq'] = struct.unpack("<H", raw_record[16:18])[0]
        record['link'] = struct.unpack("<H", raw_record[18:20])[0]
        record['attr_off'] = struct.unpack("<H", raw_record[20:22])[0]
        record['flags'] = struct.unpack("<H", raw_record[22:24])[0]
        record['size'] = struct.unpack("<I", raw_record[24:28])[0]
        record['alloc_sizef'] = struct.unpack("<I", raw_record[28:32])[0]
        record['base_ref'] = struct.unpack("<Q", raw_record[32:40])[0]
        record['base_seq'] = struct.unpack("<H", raw_record[40:42])[0]
        record['next_attrid'] = struct.unpack("<H", raw_record[42:44])[0]
        record['f1'] = raw_record[44:46]  # Padding
        record['recordnum'] = struct.unpack("<I", raw_record[44:48])[0]  # Number of this MFT Record
        record['fncnt'] = 0  # Counter for number of FN attributes

    async def _parse_attribute(self, record: Dict[str, Any], attr_raw: bytes):
        attr_type = struct.unpack("<I", attr_raw[:4])[0]
        attr_len = struct.unpack("<I", attr_raw[4:8])[0]
        
        if attr_type == 0x10:  
            await self._parse_standard_information(record, attr_raw[24:])
        elif attr_type == 0x30:  
            await self._parse_file_name(record, attr_raw[24:])
        elif attr_type == 0x80:  
            record['data'] = True
        elif attr_type == 0x90:  
            record['indexroot'] = True
        elif attr_type == 0xA0:  
            record['indexallocation'] = True
        elif attr_type == 0xB0:  
            record['bitmap'] = True
        elif attr_type == 0x100: 
            record['loggedutility'] = True
        

    async def _parse_standard_information(self, record: Dict[str, Any], attr_content: bytes):
        record['si'] = {}
        record['si']['crtime'] = WindowsTime(struct.unpack("<Q", attr_content[:8])[0], self.options.localtz)
        record['si']['mtime'] = WindowsTime(struct.unpack("<Q", attr_content[8:16])[0], self.options.localtz)
        record['si']['ctime'] = WindowsTime(struct.unpack("<Q", attr_content[16:24])[0], self.options.localtz)
        record['si']['atime'] = WindowsTime(struct.unpack("<Q", attr_content[24:32])[0], self.options.localtz)
        record['si']['dos'] = struct.unpack("<I", attr_content[32:36])[0]
        record['si']['maxver'] = struct.unpack("<I", attr_content[36:40])[0]
        record['si']['ver'] = struct.unpack("<I", attr_content[40:44])[0]
        record['si']['class_id'] = struct.unpack("<I", attr_content[44:48])[0]

    async def _parse_file_name(self, record: Dict[str, Any], attr_content: bytes):
        fn = {}
        fn['par_ref'] = struct.unpack("<Q", attr_content[:8])[0]
        fn['crtime'] = WindowsTime(struct.unpack("<Q", attr_content[8:16])[0], self.options.localtz)
        fn['mtime'] = WindowsTime(struct.unpack("<Q", attr_content[16:24])[0], self.options.localtz)
        fn['ctime'] = WindowsTime(struct.unpack("<Q", attr_content[24:32])[0], self.options.localtz)
        fn['atime'] = WindowsTime(struct.unpack("<Q", attr_content[32:40])[0], self.options.localtz)
        fn['alloc_fsize'] = struct.unpack("<q", attr_content[40:48])[0]
        fn['real_fsize'] = struct.unpack("<q", attr_content[48:56])[0]
        fn['flags'] = struct.unpack("<I", attr_content[56:60])[0]
        fn['nlen'] = struct.unpack("B", attr_content[64:65])[0]
        fn['nspace'] = struct.unpack("B", attr_content[65:66])[0]

        bytes_left = fn['nlen'] * 2
        if len(attr_content) < 66 + bytes_left:
            record['notes'] += "Filename attribute data incomplete | "
        else:
            try:
                fn['name'] = attr_content[66:66+bytes_left].decode('utf-16-le')
            except UnicodeDecodeError:
                fn['name'] = attr_content[66:66+bytes_left].decode('utf-16-le', errors='replace')
                record['notes'] += "Filename attribute had some invalid Unicode characters | "

        record['fn', record['fncnt']] = fn
        record['fncnt'] += 1

        if record['fncnt'] == 1:
            record['filename'] = fn['name']

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

    async def _parse_attribute(self, record: Dict[str, Any], attr_raw: bytes, attr_header: Dict[str, Any]):
        attr_type = attr_header['type']
        
        if attr_type == 0x10:  # Standard Information
            record['si'] = self.attribute_parser.parse_standard_information(attr_raw[attr_header['soff']:])
        elif attr_type == 0x30:  # File Name
            fn_attr = self.attribute_parser.parse_file_name(attr_raw[attr_header['soff']:])
            record['fn', record['fncnt']] = fn_attr
            record['fncnt'] += 1
            if record['fncnt'] == 1:
                record['filename'] = fn_attr['name']
        elif attr_type == 0x20:  # Attribute List
            record['al'] = self.attribute_parser.parse_attribute_list(attr_raw[attr_header['soff']:])
        elif attr_type == 0x40:  # Object ID
            record['objid'] = self.attribute_parser.parse_object_id(attr_raw[attr_header['soff']:])
        elif attr_type == 0x70:  # Volume Name
            record['volname'] = True
        elif attr_type == 0x80:  # Data
            record['data'] = True
        elif attr_type == 0x90:  # Index Root
            record['indexroot'] = True
        elif attr_type == 0xA0:  # Index Allocation
            record['indexallocation'] = True
        elif attr_type == 0xB0:  # Bitmap
            record['bitmap'] = True
        elif attr_type == 0x100:  # Logged Utility Stream
            record['loggedutility'] = True

    async def _check_usec_zero(self, record: Dict[str, Any]):
        if 'si' in record:
            si_times = [record['si'][key] for key in ['crtime', 'mtime', 'atime', 'ctime']]
            record['usec-zero'] = all(isinstance(time, WindowsTime) and time.unixtime % 1 == 0 for time in si_times)
            self.logger.debug(f"Record {record['recordnum']} usec-zero: {record['usec-zero']}")

    async def generate_filepaths(self):
        for i in self.mft:
            if self.mft[i]['filename'] == '':
                if self.mft[i]['fncnt'] > 0:
                    await self.get_folder_path(i)
                else:
                    self.mft[i]['filename'] = 'NoFNRecord'

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
