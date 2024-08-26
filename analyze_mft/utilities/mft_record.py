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
            if not await self._parse_header():
                return None
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

    async def _parse_header(self) -> bool:
        try:
            if len(self.raw_record) < 56:
                raise ValueError(f"Insufficient data for MFT header: {len(self.raw_record)} bytes")
            
            self.header = MFTHeader(
                magic=int.from_bytes(self.raw_record[:4], byteorder='little'),
                upd_off=int.from_bytes(self.raw_record[4:6], byteorder='little'),
                upd_cnt=int.from_bytes(self.raw_record[6:8], byteorder='little'),
                lsn=struct.unpack("<d", self.raw_record[8:16])[0],
                seq=int.from_bytes(self.raw_record[16:18], byteorder='little'),
                link=int.from_bytes(self.raw_record[18:20], byteorder='little'),
                attr_off=int.from_bytes(self.raw_record[20:22], byteorder='little'),
                flags=int.from_bytes(self.raw_record[22:24], byteorder='little'),
                size=int.from_bytes(self.raw_record[24:28], byteorder='little'),
                alloc_sizef=int.from_bytes(self.raw_record[28:32], byteorder='little'),
                base_ref=int.from_bytes(self.raw_record[32:40], byteorder='little'),
                base_seq=int.from_bytes(self.raw_record[40:42], byteorder='little'),
                next_attrid=int.from_bytes(self.raw_record[42:44], byteorder='little'),
                f1=self.raw_record[44:46],
                recordnum=int.from_bytes(self.raw_record[46:50], byteorder='little')
            )
            return True
        except struct.error as e:
            self.logger.error(f"Error parsing MFT header: {str(e)}")
            return False


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
            
    async def _parse_attributes(self) -> None:
        if not self.header:
            raise ValueError("Header must be parsed before attributes")
        
        offset = self.header.attr_off
        self.logger.debug(f"Starting attribute parsing at offset: {offset}")
        
        while offset < len(self.raw_record):
            try:
                attr_type = int.from_bytes(self.raw_record[offset:offset+4], byteorder='little')
                if attr_type == 0xFFFFFFFF:
                    self.logger.debug("Reached end of attributes marker")
                    break
                attr_len = int.from_bytes(self.raw_record[offset+4:offset+8], byteorder='little')
                self.logger.debug(f"Found attribute type: {attr_type:X}, length: {attr_len}")
                if attr_len == 0:
                    self.logger.warning(f"Invalid attribute length of 0 at offset {offset}")
                    break
                
                self.attributes.append({
                    'type': attr_type,
                    'data': self.raw_record[offset:offset+attr_len]
                })
                
                offset += attr_len
            except IndexError:
                self.logger.warning(f"Error parsing attribute at offset {offset}")
                break
        
        self.logger.debug(f"Parsed {len(self.attributes)} attributes")

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