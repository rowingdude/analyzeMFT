import logging
import struct
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from analyze_mft.parsers.attribute_parser import AttributeParser
from analyze_mft.utilities.windows_time import WindowsTime
from analyze_mft.constants.constants import *

@dataclass
class MFTHeader:
    magic: int
    upd_off: int
    upd_cnt: int
    lsn: float
    seq: int
    link: int
    attr_off: int
    flags: int
    size: int
    alloc_sizef: int
    base_ref: int
    base_seq: int
    next_attrid: int
    f1: bytes
    recordnum: int

class MFTRecord:
    def __init__(self, raw_record: bytes, options: Dict[str, Any]):
        self.raw_record = raw_record
        self.options = options
        self.logger = logging.getLogger('analyzeMFT')
        self.header: Optional[MFTHeader] = None
        self.attributes: List[Dict[str, Any]] = []

    async def parse(self) -> Optional[Dict[str, Any]]:
        try:
            self.logger.debug("Starting MFTRecord parse")
            await self._parse_header()
            await self._parse_attributes()
            return {
                'recordnum': self.header.recordnum if self.header else 0,
                'seq': self.header.seq if self.header else 0,
                'flags': self.header.flags if self.header else 0,
                'attributes': self.attributes
            }
        except Exception as e:
            self.logger.error(f"Error parsing MFT record: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None

    async def _parse_header(self) -> None:
        if len(self.raw_record) < 56:
            raise ValueError(f"Insufficient data for MFT header: {len(self.raw_record)} bytes")
        
        self.header = MFTHeader(
            magic=struct.unpack("<I", self.raw_record[:4])[0],
            upd_off=struct.unpack("<H", self.raw_record[4:6])[0],
            upd_cnt=struct.unpack("<H", self.raw_record[6:8])[0],
            lsn=struct.unpack("<d", self.raw_record[8:16])[0],
            seq=struct.unpack("<H", self.raw_record[16:18])[0],
            link=struct.unpack("<H", self.raw_record[18:20])[0],
            attr_off=struct.unpack("<H", self.raw_record[20:22])[0],
            flags=struct.unpack("<H", self.raw_record[22:24])[0],
            size=struct.unpack("<I", self.raw_record[24:28])[0],
            alloc_sizef=struct.unpack("<I", self.raw_record[28:32])[0],
            base_ref=struct.unpack("<Q", self.raw_record[32:40])[0],
            base_seq=struct.unpack("<H", self.raw_record[40:42])[0],
            next_attrid=struct.unpack("<H", self.raw_record[42:44])[0],
            f1=self.raw_record[44:46],
            recordnum=struct.unpack("<I", self.raw_record[46:50])[0]
        )

    async def _parse_attributes(self) -> None:
        if not self.header:
            raise ValueError("Header must be parsed before attributes")
        
        offset = self.header.attr_off
        self.logger.debug(f"Starting attribute parsing at offset: {offset}")
        
        while offset < len(self.raw_record):
            try:
                attr_type = struct.unpack("<I", self.raw_record[offset:offset+4])[0]
                if attr_type == 0xFFFFFFFF:
                    self.logger.debug("Reached end of attributes marker")
                    break
                
                attr_len = struct.unpack("<I", self.raw_record[offset+4:offset+8])[0]
                self.logger.debug(f"Found attribute type: {attr_type:X}, length: {attr_len}")
                
                if attr_len == 0:
                    self.logger.warning(f"Invalid attribute length of 0 at offset {offset}")
                    break
                
                attr_data = self.raw_record[offset:offset+attr_len]
                self.attributes.append({
                    'type': attr_type,
                    'data': attr_data
                })
                
                offset += attr_len
            except struct.error:
                self.logger.warning(f"Error parsing attribute at offset {offset}")
                break
        
        self.logger.debug(f"Parsed {len(self.attributes)} attributes")

    async def _parse_attribute(self, attr_type: int, attr_data: bytes, attribute_parser: AttributeParser) -> Optional[Dict[str, Any]]:
        attr_header = await attribute_parser.parse_attribute_header()
        if not attr_header:
            self.logger.warning(f"Failed to parse attribute header for type {attr_type}")
            return None

        content_offset = attr_header.get('content_offset')
        if content_offset is None:
            content_offset = attr_header.get('data_runs_offset', 0)

        try:
            if attr_type == STANDARD_INFORMATION:
                return await attribute_parser.parse_standard_information(content_offset)
            elif attr_type == FILE_NAME:
                return await attribute_parser.parse_file_name(content_offset)
            elif attr_type == OBJECT_ID:
                return await attribute_parser.parse_object_id(content_offset)
            elif attr_type == DATA:
                return {'present': True}
            elif attr_type == INDEX_ROOT:
                return await attribute_parser.parse_index_root(content_offset)
            elif attr_type == INDEX_ALLOCATION:
                return await attribute_parser.parse_index_allocation(content_offset)
            elif attr_type == BITMAP:
                return {'present': True}
            elif attr_type == LOGGED_UTILITY_STREAM:
                return {'present': True}
            else:
                return {'type': attr_type, 'data': attr_data}
        except Exception as e:
            self.logger.error(f"Error parsing attribute {attr_type}: {str(e)}")
            return None

    async def _create_record_dict(self) -> Dict[str, Any]:
        return {
            'recordnum': self.header.recordnum,
            'seq': self.header.seq,
            'flags': self.header.flags,
            'attributes': self.attributes
        }

    @property
    def record_number(self) -> int:
        return self.header.recordnum if self.header else -1

    @property
    def filename(self) -> str:
        for attr_type, attr_data in self.attributes.items():
            if attr_type == FILE_NAME:
                return attr_data.get('name', '')
        return ''