#!/usr/bin/env python

# Version 2.1.1.1
#
# Author: Benjamin Cance (bjc@tdx.li)
# Copyright Benjamin Cance 2024
#
# 2-Aug-24 
# - Updating to current PEP

from argparse import ArgumentParser
from typing import Dict, Any
from . import mftutils
from .mft_formatter import mft_to_csv, mft_to_body, mft_to_l2t
from .mftutils import decodeMFTmagic, decodeMFTisactive, decodeMFTrecordtype, decodeVolumeInfo, decodeObjectID, ObjectID

def set_default_options() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("--debug", action="store_true", default=False)
    parser.add_argument("--localtz", default=None)
    parser.add_argument("--bodystd", action="store_true", default=False)
    parser.add_argument("--bodyfull", action="store_true", default=False)
    return parser

def decodeMFTmagic(record: Dict[str, Any]) -> str:
    magic_values = {
        0x454c4946: "Good",
        0x44414142: 'Bad',
        0x00000000: 'Zero'
    }
    return magic_values.get(record['magic'], 'Unknown')

def decodeMFTisactive(record: Dict[str, Any]) -> str:
    return 'Active' if record['flags'] & 0x0001 else 'Inactive'


def decodeMFTrecordtype(record: Dict[str, Any]) -> str:
    flags = int(record['flags'])
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

