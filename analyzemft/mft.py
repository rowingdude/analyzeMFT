#!/usr/bin/env python3

# Version 2.2
#
# Author: Benjamin Cance (bjc@tdx.li)
# Copyright Benjamin Cance 2024
#
# 3-Aug-24 
# - Updated to Python 3 and optimized

import struct
from typing import Dict, Any, List, Union, Tuple
from argparse import ArgumentParser
from collections import namedtuple
from . import mftutils

# Define constants
ATTRIBUTE_TYPES = {
    0x10: "STANDARD_INFORMATION",
    0x20: "ATTRIBUTE_LIST",
    0x30: "FILE_NAME",
    0x40: "OBJECT_ID",
    0x50: "SECURITY_DESCRIPTOR",
    0x60: "VOLUME_NAME",
    0x70: "VOLUME_INFORMATION",
    0x80: "DATA",
    0x90: "INDEX_ROOT",
    0xA0: "INDEX_ALLOCATION",
    0xB0: "BITMAP",
    0xC0: "REPARSE_POINT",
    0xD0: "EA_INFORMATION",
    0xE0: "EA",
    0xF0: "PROPERTY_SET",
    0x100: "LOGGED_UTILITY_STREAM",
}

# Define structs for better memory usage and performance
MFTHeader = namedtuple('MFTHeader', ['magic', 'upd_off', 'upd_cnt', 'lsn', 'seq', 'link', 'attr_off', 'flags', 'size', 'alloc_sizef', 'base_ref', 'next_attrid', 'f1', 'recordnum'])
ATRHeader = namedtuple('ATRHeader', ['type', 'len', 'res', 'nlen', 'name_off', 'flags', 'id', 'ssize', 'soff', 'idxflag', 'start_vcn', 'last_vcn', 'run_off', 'compusize', 'f1', 'alen', 'initsize'])

def set_default_options() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("--debug", action="store_true", default=False)
    parser.add_argument("--localtz", default=None)
    parser.add_argument("--bodystd", action="store_true", default=False)
    parser.add_argument("--bodyfull", action="store_true", default=False)
    return parser

def parse_record(raw_record: bytes, options: Any) -> Dict[str, Any]:
    record: Dict[str, Any] = {'filename': '', 'notes': '', 'fncnt': 0}

    if len(raw_record) < 48:
        record['corrupt'] = True
        record['notes'] = "Incomplete MFT record"
        return record

    header = decodeMFTHeader(raw_record)
    record.update(header._asdict())

    if options.debug:
        print(f"DEBUG: Record number: {record['recordnum']}")
        print(f"DEBUG: Magic: {record['magic']} Attribute offset: {record['attr_off']} Flags: {hex(int(record['flags']))} Size: {record['size']}")

    if record['magic'] == 0x44414142:
        record['baad'] = True
        return record

    if record['magic'] != 0x454c4946:
        record['corrupt'] = True
        return record

    read_ptr = record['attr_off']

    while read_ptr < len(raw_record):
        ATRrecord = decodeATRHeader(raw_record[read_ptr:])
        if ATRrecord.type == 0xffffffff:  # End of attributes
            break

        if options.debug:
            print(f"DEBUG: Attribute type: {ATRrecord.type:x} Length: {ATRrecord.len} Res: {ATRrecord.res:x}")

        if ATRrecord.len == 0:
            record['corrupt'] = True
            record['notes'] = f"{record.get('notes', '')} Zero length attribute"
            break

        attr_offset = ATRrecord.soff if ATRrecord.soff is not None else 0
        attr_data = raw_record[read_ptr + attr_offset:]

        process_attribute(record, ATRrecord, attr_data, options)

        if ATRrecord.len > 0:
            read_ptr += ATRrecord.len
        else:
            break  # Avoid infinite loop if length is 0

    return record

def process_attribute(record: Dict[str, Any], ATRrecord: ATRHeader, attr_data: bytes, options: Any) -> None:
    attr_processors = {
        0x10: lambda: record.update({'si': decodeSIAttribute(attr_data, options.localtz)}),
        0x20: lambda: record.update({'al': decodeAttributeList(attr_data, record) if ATRrecord.res == 0 else None}),
        0x30: lambda: process_fn_attribute(record, attr_data, options),
        0x40: lambda: record.update({'objid': decodeObjectID(attr_data)}),
        0x70: lambda: record.update({'volinfo': decodeVolumeInfo(attr_data, options)}),
    }

    processor = attr_processors.get(ATRrecord.type)
    if processor:
        processor()
    else:
        record[ATTRIBUTE_TYPES.get(ATRrecord.type, f"Unknown_{ATRrecord.type:x}")] = True

def process_fn_attribute(record: Dict[str, Any], attr_data: bytes, options: Any) -> None:
    try:
        FNrecord = decodeFNAttribute(attr_data, options.localtz, record)
        if 'par_ref' not in FNrecord:
            FNrecord['par_ref'] = 'N/A'
        if 'par_seq' not in FNrecord:
            FNrecord['par_seq'] = 'N/A'
        record[('fn', record['fncnt'])] = FNrecord
        record['fncnt'] += 1
    except Exception as e:
        error_msg = f"Error processing FN attribute: {str(e)}"
        record['notes'] = f"{record.get('notes', '')} {error_msg}"
        if options.debug:
            print(f"DEBUG: {error_msg}")
            print(f"DEBUG: FN attribute data length: {len(attr_data)}")
            print(f"DEBUG: First 16 bytes of FN attribute data: {attr_data[:16].hex()}")

def decodeMFTHeader(raw_record: bytes) -> MFTHeader:
    return MFTHeader._make(struct.unpack("<IHHqHHHHIIqHHI", raw_record[:48]))

def decodeATRHeader(s: bytes) -> ATRHeader:
    # Ensure we have at least 16 bytes to work with
    if len(s) < 16:
        # Not enough data to unpack, return a dummy ATRHeader
        return ATRHeader(type=0xffffffff, len=0, res=0, nlen=0, name_off=0, flags=0, id=0, 
                         ssize=None, soff=None, idxflag=None, start_vcn=None, last_vcn=None, 
                         run_off=None, compusize=None, f1=None, alen=None, initsize=None)
    
    # Manually unpack the first 16 bytes
    type_code = int.from_bytes(s[0:4], byteorder='little')
    length = int.from_bytes(s[4:8], byteorder='little')
    res = int.from_bytes(s[8:12], byteorder='little')
    nlen = int.from_bytes(s[12:13], byteorder='little')
    name_off = int.from_bytes(s[13:14], byteorder='little')
    flags = int.from_bytes(s[14:16], byteorder='little')
    
    # If it's the end of attributes marker, return early
    if type_code == 0xffffffff:
        return ATRHeader(type=0xffffffff, len=0, res=0, nlen=0, name_off=0, flags=0, id=0, 
                         ssize=None, soff=None, idxflag=None, start_vcn=None, last_vcn=None, 
                         run_off=None, compusize=None, f1=None, alen=None, initsize=None)
    
    # Try to get the 'id' field if we have enough data
    id_value = int.from_bytes(s[16:18], byteorder='little') if len(s) >= 18 else 0
    
    if res == 0:  # Resident
        if len(s) >= 24:
            ssize = int.from_bytes(s[18:22], byteorder='little')
            soff = int.from_bytes(s[22:24], byteorder='little')
            idxflag = int.from_bytes(s[24:26], byteorder='little') if len(s) >= 26 else 0
            return ATRHeader(type_code, length, res, nlen, name_off, flags, id_value, 
                             ssize, soff, idxflag, None, None, None, None, None, None, None)
        else:
            return ATRHeader(type_code, length, res, nlen, name_off, flags, id_value, 
                             None, None, None, None, None, None, None, None, None, None)
    else:  # Non-resident
        if len(s) >= 64:
            start_vcn = struct.unpack("<d", s[18:26])[0]
            last_vcn = struct.unpack("<d", s[26:34])[0]
            run_off = int.from_bytes(s[34:36], byteorder='little')
            compusize = int.from_bytes(s[36:38], byteorder='little')
            f1 = int.from_bytes(s[38:42], byteorder='little')
            alen = struct.unpack("<d", s[42:50])[0]
            ssize = struct.unpack("<d", s[50:58])[0]
            initsize = struct.unpack("<d", s[58:66])[0]
            return ATRHeader(type_code, length, res, nlen, name_off, flags, id_value, 
                             None, None, None, start_vcn, last_vcn, run_off, compusize, f1, alen, initsize)
        else:
            return ATRHeader(type_code, length, res, nlen, name_off, flags, id_value, 
                             None, None, None, None, None, None, None, None, None, None)

def decodeSIAttribute(s: bytes, localtz) -> Dict[str, Any]:
    d = {}
    min_size = 48  # Minimum size for the essential fields

    if len(s) < min_size:
        # Not enough data, return a partially filled or empty dictionary
        return d

    # Unpack the essential fields (48 bytes)
    essential_fields = struct.unpack("<LLLLLLLLLLLL", s[:48])
    
    for i, field in enumerate(['crtime', 'mtime', 'ctime', 'atime']):
        d[field] = mftutils.WindowsTime(essential_fields[i*2], essential_fields[i*2+1], localtz)

    d.update({
        'dos': essential_fields[8],
        'maxver': essential_fields[9],
        'ver': essential_fields[10],
        'class_id': essential_fields[11]
    })

    # If we have more data, unpack the additional fields
    remaining = len(s) - 48
    if remaining >= 4:
        d['own_id'] = struct.unpack("<I", s[48:52])[0]
    if remaining >= 8:
        d['sec_id'] = struct.unpack("<I", s[52:56])[0]
    if remaining >= 16:
        d['quota'] = struct.unpack("<Q", s[56:64])[0]
    if remaining >= 24:
        d['usn'] = struct.unpack("<Q", s[64:72])[0]


    return d
def decodeFNAttribute(s: bytes, localtz, record: Dict[str, Any]) -> Dict[str, Any]:
    d = {}
    min_size = 66  # Minimum size for all the fields we want to unpack

    if len(s) < min_size:
        record['notes'] = f"{record.get('notes', '')} Incomplete FN attribute (expected {min_size} bytes, got {len(s)})"
        return d

    try:
        fields = struct.unpack("<LHQQQQqqLBB", s[:66])
        
        d['par_ref'], d['par_seq'] = fields[0], fields[1]
        for i, field in enumerate(['crtime', 'mtime', 'ctime', 'atime']):
            d[field] = mftutils.WindowsTime(fields[i*2+2], fields[i*2+3], localtz)
        d['alloc_fsize'], d['real_fsize'], d['flags'] = fields[10], fields[11], fields[12]
        d['nlen'], d['nspace'] = fields[13], fields[14]
        
        name_length = d['nlen'] * 2  # UTF-16 characters are 2 bytes each
        if len(s) >= 66 + name_length:
            try:
                d['name'] = s[66:66+name_length].decode('utf-16-le')
            except UnicodeDecodeError:
                d['name'] = s[66:66+name_length].hex()
                record['notes'] = f"{record.get('notes', '')} Filename - chars converted to hex"
        else:
            d['name'] = ''
            record['notes'] = f"{record.get('notes', '')} Truncated filename in FN attribute"
    
    except struct.error as e:
        record['notes'] = f"{record.get('notes', '')} Error unpacking FN attribute: {str(e)}"
    
    return d
def decodeAttributeList(s: bytes, record: Dict[str, Any]) -> Dict[str, Any]:
    d = {}
    fields = struct.unpack("<IHBBQIHH", s[:26])
    d['type'], d['len'], d['nlen'], d['f1'] = fields[0], fields[1], fields[2], fields[3]
    d['start_vcn'], d['file_ref'], d['seq'], d['id'] = fields[4], fields[5], fields[6], fields[7]
    
    try:
        d['name'] = s[26:26+d['nlen']*2].decode('utf-16-le')
    except UnicodeDecodeError:
        d['name'] = s[26:26+d['nlen']*2].hex()
        add_note(record, 'Attribute List - chars converted to hex')
    
    return d

def decodeVolumeInfo(s: bytes, options) -> Dict[str, Any]:
    d = {}
    fields = struct.unpack("<dBBHI", s[:16])
    d['f1'], d['maj_ver'], d['min_ver'], d['flags'], d['f2'] = fields

    if options.debug:
        print(f"+Volume Info")
        print(f"++F1: {d['f1']}")
        print(f"++Major Version: {d['maj_ver']}")
        print(f"++Minor Version: {d['min_ver']}")
        print(f"++Flags: {d['flags']}")
        print(f"++F2: {d['f2']}")

    return d

def decodeObjectID(s: bytes) -> Dict[str, Any]:
    return {
        'objid': ObjectID(s[0:16]),
        'orig_volid': ObjectID(s[16:32]),
        'orig_objid': ObjectID(s[32:48]),
        'orig_domid': ObjectID(s[48:64])
    }

def ObjectID(s: bytes) -> str:
    return 'Undefined' if s == b'\x00' * 16 else f"{s[:4].hex()}-{s[4:6].hex()}-{s[6:8].hex()}-{s[8:10].hex()}-{s[10:16].hex()}"

def add_note(record: Dict[str, Any], s: str) -> None:
    record['notes'] = f"{record.get('notes', '')} | {s} |".strip()

def mft_to_csv(record: Dict[str, Any], ret_header: bool) -> List[str]:
    if ret_header:
        return [
            'Record Number', 'Good', 'Active', 'Record type',
            'Sequence Number', 'Parent File Rec. #', 'Parent File Rec. Seq. #',
            'Filename #1', 'Std Info Creation date', 'Std Info Modification date',
            'Std Info Access date', 'Std Info Entry date', 'FN Info Creation date',
            'FN Info Modification date', 'FN Info Access date', 'FN Info Entry date',
            'Object ID', 'Birth Volume ID', 'Birth Object ID', 'Birth Domain ID',
            'Filename #2', 'FN Info Creation date', 'FN Info Modify date',
            'FN Info Access date', 'FN Info Entry date', 'Filename #3', 'FN Info Creation date',
            'FN Info Modify date', 'FN Info Access date', 'FN Info Entry date', 'Filename #4',
            'FN Info Creation date', 'FN Info Modify date', 'FN Info Access date',
            'FN Info Entry date', 'Standard Information', 'Attribute List', 'Filename',
            'Object ID', 'Volume Name', 'Volume Info', 'Data', 'Index Root',
            'Index Allocation', 'Bitmap', 'Reparse Point', 'EA Information', 'EA',
            'Property Set', 'Logged Utility Stream', 'Log/Notes', 'STF FN Shift', 'uSec Zero'
        ]

    if 'baad' in record:
        return [str(record.get('recordnum', '')), "BAAD MFT Record"]

    csv_string = [
        record.get('recordnum', ''),
        decodeMFTmagic(record),
        decodeMFTisactive(record),
        decodeMFTrecordtype(record),
        str(record.get('seq', ''))
    ]

    if 'corrupt' in record:
        return csv_string + [str(record.get('recordnum', '')), "Corrupt", "Corrupt", "Corrupt MFT Record"]

    csv_string.append(str(record.get('seq', '')))

    if record.get('fncnt', 0) > 0 and ('fn', 0) in record:
        fn_record = record['fn', 0]
        csv_string.extend([str(fn_record.get('par_ref', 'N/A')), str(fn_record.get('par_seq', 'N/A'))])
    else:
        csv_string.extend(['NoParent', 'NoParent'])

    if record.get('fncnt', 0) > 0 and 'si' in record:
        fn_record = record['fn', 0]
        si_record = record['si']
        filenameBuffer = [
            record.get('filename', ''),
            str(getattr(si_record.get('crtime', ''), 'dtstr', 'N/A')),
            getattr(si_record.get('mtime', ''), 'dtstr', 'N/A'),
            getattr(si_record.get('atime', ''), 'dtstr', 'N/A'),
            getattr(si_record.get('ctime', ''), 'dtstr', 'N/A'),
            getattr(fn_record.get('crtime', ''), 'dtstr', 'N/A'),
            getattr(fn_record.get('mtime', ''), 'dtstr', 'N/A'),
            getattr(fn_record.get('atime', ''), 'dtstr', 'N/A'),
            getattr(fn_record.get('ctime', ''), 'dtstr', 'N/A')
        ]
    elif 'si' in record:
        si_record = record['si']
        filenameBuffer = [
            'NoFNRecord',
            str(getattr(si_record.get('crtime', ''), 'dtstr', 'N/A')),
            getattr(si_record.get('mtime', ''), 'dtstr', 'N/A'),
            getattr(si_record.get('atime', ''), 'dtstr', 'N/A'),
            getattr(si_record.get('ctime', ''), 'dtstr', 'N/A'),
            'NoFNRecord', 'NoFNRecord', 'NoFNRecord', 'NoFNRecord'
        ]
    else:
        filenameBuffer = ['NoFNRecord', 'NoSIRecord', 'NoSIRecord', 'NoSIRecord', 'NoSIRecord',
                          'NoFNRecord', 'NoFNRecord', 'NoFNRecord', 'NoFNRecord']

    csv_string.extend(filenameBuffer)

    if 'objid' in record:
        objid_record = record['objid']
        objidBuffer = [
            objid_record.get('objid', ''),
            objid_record.get('orig_volid', ''),
            objid_record.get('orig_objid', ''),
            objid_record.get('orig_domid', '')
        ]
    else:
        objidBuffer = ['', '', '', '']

    csv_string.extend(objidBuffer)

    for i in range(1, record.get('fncnt', 0)):
        if ('fn', i) in record:
            fn_record = record['fn', i]
            filenameBuffer = [
                fn_record.get('name', ''),
                getattr(fn_record.get('crtime', ''), 'dtstr', 'N/A'),
                getattr(fn_record.get('mtime', ''), 'dtstr', 'N/A'),
                getattr(fn_record.get('atime', ''), 'dtstr', 'N/A'),
                getattr(fn_record.get('ctime', ''), 'dtstr', 'N/A')
            ]
        else:
            filenameBuffer = ['', '', '', '', '']
        csv_string.extend(filenameBuffer)

    # Pad with empty strings if we have less than 3 additional filenames
    csv_string.extend([''] * (15 - 5 * (record.get('fncnt', 1) - 1)))

    for attr in ['si', 'al', 'objid', 'volname', 'volinfo', 'data', 'indexroot', 'indexallocation', 'bitmap', 'reparse', 'eainfo', 'ea', 'propertyset', 'loggedutility']:
        csv_string.append('True' if attr in record else 'False')

    csv_string.append(record.get('notes', 'None'))
    csv_string.append('Y' if 'stf-fn-shift' in record else 'N')
    csv_string.append('Y' if 'usec-zero' in record else 'N')

    return csv_string
def mft_to_body(record: Dict[str, Any], full: bool, std: bool) -> str:
    if record['fncnt'] > 0:
        name = record['filename'] if full else record['fn',0]['name']
        
        if std:
            return f"0|{name}|0|0|0|0|{int(record['fn',0]['real_fsize'])}|{int(record['si']['atime'].unixtime)}|{int(record['si']['mtime'].unixtime)}|{int(record['si']['ctime'].unixtime)}|{int(record['si']['ctime'].unixtime)}\n"
        else:
            return f"0|{name}|0|0|0|0|{int(record['fn',0]['real_fsize'])}|{int(record['fn',0]['atime'].unixtime)}|{int(record['fn',0]['mtime'].unixtime)}|{int(record['fn',0]['ctime'].unixtime)}|{int(record['fn',0]['crtime'].unixtime)}\n"
    
    elif 'si' in record:
        return f"0|No FN Record|0|0|0|0|0|{int(record['si']['atime'].unixtime)}|{int(record['si']['mtime'].unixtime)}|{int(record['si']['ctime'].unixtime)}|{int(record['si']['ctime'].unixtime)}\n"
    
    else:
        return "0|Corrupt Record|0|0|0|0|0|0|0|0|0\n"

def mft_to_l2t(record: Dict[str, Any]) -> str:
    if record['fncnt'] > 0:
        return ''.join(_generate_l2t_entries(record, 'fn', 0))
    elif 'si' in record:
        return ''.join(_generate_l2t_entries(record, 'si'))
    else:
        return "-|-|TZ|unknown time|FILE|NTFS $MFT|unknown time|user|host|Corrupt Record|desc|version|NoFNRecord|{record['seq']}|-|format|extra\n"

def _generate_l2t_entries(record: Dict[str, Any], attr_type: str, index: int = None) -> List[str]:
    entries = []
    for i in ('atime', 'mtime', 'ctime', 'crtime'):
        date, time = record[attr_type][index][i].dtstr.split(' ') if index is not None else record[attr_type][i].dtstr.split(' ')
        type_str = f"${attr_type.upper()} [{'.A..' if i == 'atime' else 'M...' if i == 'mtime' else '..C.' if i == 'ctime' else '...B'}] time"
        macb_str = '.A..' if i == 'atime' else 'M...' if i == 'mtime' else '..C.' if i == 'ctime' else '...B'
        entries.append(f"{date}|{time}|TZ|{macb_str}|FILE|NTFS $MFT|{type_str}|user|host|{record['filename']}|desc|version|{record['filename']}|{record['seq']}|{record['notes']}|format|extra\n")
    return entries

def decodeMFTmagic(record: Dict[str, Any]) -> str:
    magic_values = {0x454c4946: "Good", 0x44414142: 'Bad', 0x00000000: 'Zero'}
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

# Main execution
if __name__ == "__main__":
    options = set_default_options().parse_args()