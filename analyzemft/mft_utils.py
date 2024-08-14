#!/usr/bin/env python

# Version 2.1.1
#
# Author: Benjamin Cance (bjc@tdx.li)
# Copyright Benjamin Cance 2024

import logging
from datetime import datetime, timezone, MINYEAR, MAXYEAR
from typing import Union, Dict, Any
import struct
from enum import Enum

class WindowsTime:
    def __init__(self, timestamp: int, localtz: bool = False):
        self.timestamp = int(timestamp)
        self.localtz = localtz
        self.dtstr: str = ""
        self.unixtime: float = 0.0
        self.logger = logging.getLogger(__name__)

        if self.timestamp == 0:
            self.dtstr = "Not defined (Zero)"
            return

        try:
            if not self.is_valid_timestamp():
                raise ValueError(f"Timestamp out of valid range: {self.timestamp}")
            
            self.unixtime = self.get_unix_time()
            dt = datetime.fromtimestamp(self.unixtime, tz=timezone.utc if not self.localtz else None)
            if MINYEAR <= dt.year <= MAXYEAR:
                self.dtstr = dt.isoformat(' ')
            else:
                self.dtstr = f"Out of range: {self.timestamp}"
        except Exception as e:
            self.logger.warning(f"Error converting timestamp {self.timestamp}: {str(e)}")
            self.dtstr = f"Invalid: {self.timestamp} ({str(e)})"

    def is_valid_timestamp(self) -> bool:
        return 0 <= self.timestamp <= (2**63 - 1)

    def get_unix_time(self) -> float:
        return (self.timestamp / 10000000) - 11644473600

    def __str__(self):
        return self.dtstr

class MagicValues(Enum):
    GOOD = 0x454c4946
    BAD = 0x44414142
    ZERO = 0x00000000

def decodeMFTmagic(record: Dict[str, Any]) -> str:
    magic = record.get('magic', 0)
    return MagicValues(magic).name if magic in MagicValues._value2member_map_ else 'Unknown'

def decodeMFTisactive(record: Dict[str, Any]) -> str:
    return 'Active' if record.get('flags', 0) & 0x0001 else 'Inactive'

def decodeMFTrecordtype(record: Dict[str, Any]) -> str:
    flags = int(record.get('flags', 0))
    record_type = 'Folder' if flags & 0x0002 else 'File'
    if flags & 0x0004:
        record_type += ' + Unknown1'
    if flags & 0x0008:
        record_type += ' + Unknown2'
    return record_type

def decodeVolumeInfo(s: bytes, logger: logging.Logger) -> Dict[str, Any]:
    d = {}
    try:
        d['f1'] = struct.unpack("<d", s[:8])[0]
        d['maj_ver'] = struct.unpack("B", s[8:9])[0]
        d['min_ver'] = struct.unpack("B", s[9:10])[0]
        d['flags'] = struct.unpack("<H", s[10:12])[0]
        d['f2'] = struct.unpack("<I", s[12:16])[0]
        
        logger.debug(f"+Volume Info: F1={d['f1']}, Major Version={d['maj_ver']}, "
                     f"Minor Version={d['min_ver']}, Flags={d['flags']}, F2={d['f2']}")
    except struct.error as e:
        logger.error(f"Error decoding Volume Info: {str(e)}")
        d = {'error': str(e)}
    return d

def decodeObjectID(s: bytes) -> Dict[str, str]:
    return {
        'objid': ObjectID(s[0:16]),
        'orig_volid': ObjectID(s[16:32]),
        'orig_objid': ObjectID(s[32:48]),
        'orig_domid': ObjectID(s[48:64])
    }

def ObjectID(s: bytes) -> str:
    if s == b'\x00' * 16:
        return 'Undefined'
    return f"{s[:4].hex()}-{s[4:6].hex()}-{s[6:8].hex()}-{s[8:10].hex()}-{s[10:16].hex()}"
