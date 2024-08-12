#!/usr/bin/env python

# Version 2.1.1
#
# Author: Benjamin Cance (bjc@tdx.li)
# Copyright Benjamin Cance 2024
#
# 2-Aug-24 
# - Updating to current PEP
# - Correctly calculate the Unix timestamp from Windows filetime

from datetime import datetime, timezone
from typing import Union, Dict, Any
import struct
import logging
from enum import Enum

class WindowsTime:
    def __init__(self, low: int, high: int, localtz: bool):
        self.low = int(low)
        self.high = int(high)
        self.dt: Union[datetime, int] = 0
        self.dtstr: str = ""
        self.unixtime: float = 0.0

        if (low == 0) and (high == 0):
            self.dtstr = "Not defined"
            return

        try:
            self.unixtime = self.get_unix_time()
            self.dt = datetime.fromtimestamp(self.unixtime, tz=timezone.utc if not localtz else None)
            self.dtstr = self.dt.isoformat(' ')

        except (OverflowError, OSError) as e:
            logging.error(f"Error converting timestamp: {e}")
            self.dtstr = "Invalid timestamp"
            self.unixtime = 0.0

    def get_unix_time(self) -> float:
        wintime = (self.high << 32) | self.low
        return wintime / 10000000 - 11644473600

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

def decodeVolumeInfo(s,options):

    d = {}
    d['f1'] = struct.unpack("<d",s[:8])[0]                  # 8
    d['maj_ver'] = struct.unpack("B",s[8])[0]               # 1
    d['min_ver'] = struct.unpack("B",s[9])[0]               # 1
    d['flags'] = struct.unpack("<H",s[10:12])[0]            # 2
    d['f2'] = struct.unpack("<I",s[12:16])[0]               # 4

    if options.debug:
        print(f"+Volume Info")
        print(f"++F1%d" % d['f1'])
        print(f"++Major Version: %d" % d['maj_ver'])
        print(f"++Minor Version: %d" % d['min_ver'])
        print(f"++Flags: %d" % d['flags'])
        print(f"++F2: %d" % d['f2'])

    return d

def decodeObjectID(s):

    d = {}
    d['objid'] = ObjectID(s[0:16])
    d['orig_volid'] = ObjectID(s[16:32])
    d['orig_objid'] = ObjectID(s[32:48])
    d['orig_domid'] = ObjectID(s[48:64])

    return d

def ObjectID(s: bytes) -> str:
    if s == b'\x00' * 16:
        return 'Undefined'
    return f"{s[:4].hex()}-{s[4:6].hex()}-{s[6:8].hex()}-{s[8:10].hex()}-{s[10:16].hex()}"

