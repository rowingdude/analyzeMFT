import logging
import struct
from dataclasses import dataclass
from typing import Dict, Any, Optional
from .attribute_parser import AttributeParser
from .windows_time import WindowsTime


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
        self.attributes: Dict[str, Any] = {}

    def parse(self) -> Optional[Dict[str, Any]]:
        try:
            self._parse_header()
            self._parse_attributes()
            return self._create_record_dict()
        except struct.error as e:
            self.logger.error(f"Error parsing MFT record: {str(e)}")
            return None

    def _parse_header(self) -> None:
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
            base_ref=struct.unpack("<Q", self.raw_record[32:40])[0],  # Changed to 64-bit
            base_seq=struct.unpack("<H", self.raw_record[40:42])[0],
            next_attrid=struct.unpack("<H", self.raw_record[42:44])[0],
            f1=self.raw_record[44:46],
            recordnum=struct.unpack("<I", self.raw_record[46:50])[0]
        )

    def _parse_attributes(self) -> None:
        if not self.header:
            raise ValueError("Header must be parsed before attributes")
        
        offset = self.header.attr_off
        while offset < len(self.raw_record):
            try:
                attr_type = struct.unpack("<I", self.raw_record[offset:offset+4])[0]
                if attr_type == 0xFFFFFFFF:
                    break
                attr_len = struct.unpack("<I", self.raw_record[offset+4:offset+8])[0]
                self.attributes[attr_type] = self.raw_record[offset:offset+attr_len]
                offset += attr_len
            except struct.error:
                self.logger.warning(f"Error parsing attribute at offset {offset}")
                break

    def _create_record_dict(self) -> Dict[str, Any]:
        return {
            'recordnum': self.header.recordnum,
            'seq': self.header.seq,
            'flags': self.header.flags,
            'attributes': self.attributes
        }
"""   
    def decode_mft_header(self):

            if len(self.raw_record) < 48:
                raise ValueError(f"Insufficient data for MFT header: {len(self.raw_record)} bytes")

            self.record['magic'] = struct.unpack("<I", self.raw_record[:4])[0]
            self.record['upd_off'] = struct.unpack("<H", self.raw_record[4:6])[0]
            self.record['upd_cnt'] = struct.unpack("<H", self.raw_record[6:8])[0]
            self.record['lsn'] = struct.unpack("<d", self.raw_record[8:16])[0]
            self.record['seq'] = struct.unpack("<H", self.raw_record[16:18])[0]
            self.record['link'] = struct.unpack("<H", self.raw_record[18:20])[0]
            self.record['attr_off'] = struct.unpack("<H", self.raw_record[20:22])[0]
            self.record['flags'] = struct.unpack("<H", self.raw_record[22:24])[0]
            self.record['size'] = struct.unpack("<I", self.raw_record[24:28])[0]
            self.record['alloc_sizef'] = struct.unpack("<I", self.raw_record[28:32])[0]
            self.record['base_ref'] = struct.unpack("<Lxx", self.raw_record[32:38])[0]
            self.record['base_seq'] = struct.unpack("<H", self.raw_record[38:40])[0]
            self.record['next_attrid'] = struct.unpack("<H", self.raw_record[40:42])[0]
            self.record['f1'] = self.raw_record[42:44]
            self.record['recordnum'] = struct.unpack("<I", self.raw_record[44:48])[0]




        @property
        def record_number(self) -> int:
            return self.record['recordnum']

        @property
        def filename(self) -> str:
            return self.record.get('filename', '') """