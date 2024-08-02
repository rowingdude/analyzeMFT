#!/usr/bin/env python

# Version 2.1
# Author: Benjamin Cance (bjc@tdx.li)
# Copyright Benjamin Cance 2024

import struct
from typing import Dict, Any, List
from argparse import ArgumentParser
from . import mftutils

def set_default_options() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("--debug", action="store_true", default=False)
    parser.add_argument("--localtz", default=None)
    parser.add_argument("--bodystd", action="store_true", default=False)
    parser.add_argument("--bodyfull", action="store_true", default=False)
    return parser

def parse_record(raw_record: bytes, options: Any) -> Dict[str, Any]:
    record: Dict[str, Any] = {'filename': '', 'notes': '', 'fncnt': 0}

    decodeMFTHeader(record, raw_record)

    if options.debug:
        print(f"-->Record number: {record['recordnum']}\n\tMagic: {record['magic']} Attribute offset: {record['attr_off']} Flags: {hex(int(record['flags']))} Size:{record['size']}")

    if record['magic'] == 0x44414142:
        if options.debug:
            print("BAAD MFT Record")
        record['baad'] = True
        return record

    if record['magic'] != 0x454c4946:
        if options.debug:
            print("Corrupt MFT Record")
        record['corrupt'] = True
        return record

    read_ptr = record['attr_off']

    while read_ptr < 1024:
        ATRrecord = decodeATRHeader(raw_record[read_ptr:])
        if ATRrecord['type'] == 0xffffffff:
            break

        if options.debug:
            print(f"Attribute type: {ATRrecord['type']:x} Length: {ATRrecord['len']} Res: {ATRrecord['res']:x}")

        if ATRrecord['type'] == 0x10:
            SIrecord = decodeSIAttribute(raw_record[read_ptr+ATRrecord['soff']:], options.localtz)
            record['si'] = SIrecord

        elif ATRrecord['type'] == 0x20:
            if ATRrecord['res'] == 0:
                ALrecord = decodeAttributeList(raw_record[read_ptr+ATRrecord['soff']:], record)
                record['al'] = ALrecord

        elif ATRrecord['type'] == 0x30:
            FNrecord = decodeFNAttribute(raw_record[read_ptr+ATRrecord['soff']:], options.localtz, record)
            record[('fn', record['fncnt'])] = FNrecord
            record['fncnt'] += 1

        elif ATRrecord['type'] == 0x40:
            ObjectIDRecord = decodeObjectID(raw_record[read_ptr+ATRrecord['soff']:])
            record['objid'] = ObjectIDRecord

        elif ATRrecord['type'] == 0x70:
            VolumeInfoRecord = decodeVolumeInfo(raw_record[read_ptr+ATRrecord['soff']:], options)
            record['volinfo'] = VolumeInfoRecord

        if ATRrecord['len'] > 0:
            read_ptr = read_ptr + ATRrecord['len']
        else:
            break

    return record

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
        return [str(record['recordnum']), "BAAD MFT Record"]

    csv_string = [
        record['recordnum'],
        decodeMFTmagic(record),
        decodeMFTisactive(record),
        decodeMFTrecordtype(record),
        str(record['seq'])
    ]

    if 'corrupt' in record:
        return csv_string + [str(record['recordnum']), "Corrupt", "Corrupt", "Corrupt MFT Record"]

    csv_string.append(str(record['seq']))

    csv_string.extend(get_parent_info(record))
    csv_string.extend(get_filename_info(record))
    csv_string.extend(get_objid_info(record))
    csv_string.extend(get_additional_filenames(record))
    csv_string.extend(get_attribute_flags(record))
    csv_string.extend(get_notes_and_flags(record))

    return csv_string

def get_parent_info(record: Dict[str, Any]) -> List[str]:
    if record['fncnt'] > 0:
        return [str(record['fn', 0]['par_ref']), str(record['fn', 0]['par_seq'])]
    return ['NoParent', 'NoParent']

def get_filename_info(record: Dict[str, Any]) -> List[str]:
    if record['fncnt'] > 0 and 'si' in record:
        return [
            record['filename'], str(record['si']['crtime'].dtstr),
            record['si']['mtime'].dtstr, record['si']['atime'].dtstr, record['si']['ctime'].dtstr,
            record['fn', 0]['crtime'].dtstr, record['fn', 0]['mtime'].dtstr,
            record['fn', 0]['atime'].dtstr, record['fn', 0]['ctime'].dtstr
        ]
    elif 'si' in record:
        return ['NoFNRecord'] + [str(record['si'][t].dtstr) for t in ['crtime', 'mtime', 'atime', 'ctime']] + ['NoFNRecord'] * 4
    return ['NoFNRecord', 'NoSIRecord'] * 4 + ['NoFNRecord']

def get_objid_info(record: Dict[str, Any]) -> List[str]:
    if 'objid' in record:
        return [record['objid'][key] for key in ['objid', 'orig_volid', 'orig_objid', 'orig_domid']]
    return [''] * 4

def get_additional_filenames(record: Dict[str, Any]) -> List[str]:
    result = []
    for i in range(1, record['fncnt']):
        result.extend([
            record['fn', i]['name'], record['fn', i]['crtime'].dtstr,
            record['fn', i]['mtime'].dtstr, record['fn', i]['atime'].dtstr,
            record['fn', i]['ctime'].dtstr
        ])
    
    padding = {1: 15, 2: 10, 3: 5}
    result.extend([''] * padding.get(record['fncnt'], 0))
    
    return result

def get_attribute_flags(record: Dict[str, Any]) -> List[str]:
    attributes = [
        'si', 'al', 'fncnt', 'objid', 'volname', 'volinfo', 'data',
        'indexroot', 'indexallocation', 'bitmap', 'reparse', 'eainfo',
        'ea', 'propertyset', 'loggedutility'
    ]
    return ['True' if attr in record or (attr == 'fncnt' and record[attr] > 0) else 'False' for attr in attributes]

def get_notes_and_flags(record: Dict[str, Any]) -> List[str]:
    notes = record.get('notes', 'None')
    stf_fn_shift = 'Y' if 'stf-fn-shift' in record else 'N'
    usec_zero = 'Y' if 'usec-zero' in record else 'N'
    return [notes, stf_fn_shift, usec_zero]

def add_note(record, s):
    if record['notes'] == '':
        record['notes'] = s
    else:
        record['notes'] = f"{record['notes']} | {s} |"

def decodeMFTHeader(record: Dict[str, Any], raw_record: bytes) -> None:
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
    record['base_ref'] = struct.unpack("<Lxx", raw_record[32:38])[0]
    record['base_seq'] = struct.unpack("<H", raw_record[38:40])[0]
    record['next_attrid'] = struct.unpack("<H", raw_record[40:42])[0]
    record['f1'] = raw_record[42:44]
    record['recordnum'] = struct.unpack("<I", raw_record[44:48])[0]

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

def decodeATRHeader(s):
    d = {}
    d['type'] = struct.unpack("<L", s[:4])[0]
    if d['type'] == 0xffffffff:
        return d
    d['len'] = struct.unpack("<L", s[4:8])[0]
    d['res'] = struct.unpack("B", s[8])[0]
    d['nlen'] = struct.unpack("B", s[9])[0]
    d['name_off'] = struct.unpack("<H", s[10:12])[0]
    d['flags'] = struct.unpack("<H", s[12:14])[0]
    d['id'] = struct.unpack("<H", s[14:16])[0]
    if d['res'] == 0:
        d['ssize'] = struct.unpack("<L", s[16:20])[0]
        d['soff'] = struct.unpack("<H", s[20:22])[0]
        d['idxflag'] = struct.unpack("<H", s[22:24])[0]
    else:
        d['start_vcn'] = struct.unpack("<d", s[16:24])[0]
        d['last_vcn'] = struct.unpack("<d", s[24:32])[0]
        d['run_off'] = struct.unpack("<H", s[32:34])[0]
        d['compusize'] = struct.unpack("<H", s[34:36])[0]
        d['f1'] = struct.unpack("<I", s[36:40])[0]
        d['alen'] = struct.unpack("<d", s[40:48])[0]
        d['ssize'] = struct.unpack("<d", s[48:56])[0]
        d['initsize'] = struct.unpack("<d", s[56:64])[0]
    return d

def decodeSIAttribute(s, localtz):
    d = {}
    d['crtime'] = mftutils.WindowsTime(struct.unpack("<L", s[:4])[0], struct.unpack("<L", s[4:8])[0], localtz)
    d['mtime'] = mftutils.WindowsTime(struct.unpack("<L", s[8:12])[0], struct.unpack("<L", s[12:16])[0], localtz)
    d['ctime'] = mftutils.WindowsTime(struct.unpack("<L", s[16:20])[0], struct.unpack("<L", s[20:24])[0], localtz)
    d['atime'] = mftutils.WindowsTime(struct.unpack("<L", s[24:28])[0], struct.unpack("<L", s[28:32])[0], localtz)
    d['dos'] = struct.unpack("<I", s[32:36])[0]
    d['maxver'] = struct.unpack("<I", s[36:40])[0]
    d['ver'] = struct.unpack("<I", s[40:44])[0]
    d['class_id'] = struct.unpack("<I", s[44:48])[0]
    d['own_id'] = struct.unpack("<I", s[48:52])[0]
    d['sec_id'] = struct.unpack("<I", s[52:56])[0]
    d['quota'] = struct.unpack("<d", s[56:64])[0]
    d['usn'] = struct.unpack("<d", s[64:72])[0]
    return d

def decodeFNAttribute(s, localtz, record):
    d = {}
    d['par_ref'] = struct.unpack("<Lxx", s[:6])[0]
    d['par_seq'] = struct.unpack("<H", s[6:8])[0]
    d['crtime'] = mftutils.WindowsTime(struct.unpack("<L", s[8:12])[0], struct.unpack("<L", s[12:16])[0], localtz)
    d['mtime'] = mftutils.WindowsTime(struct.unpack("<L", s[16:20])[0], struct.unpack("<L", s[20:24])[0], localtz)
    d['ctime'] = mftutils.WindowsTime(struct.unpack("<L", s[24:28])[0], struct.unpack("<L", s[28:32])[0], localtz)
    d['atime'] = mftutils.WindowsTime(struct.unpack("<L", s[32:36])[0], struct.unpack("<L", s[36:40])[0], localtz)
    d['alloc_fsize'] = struct.unpack("<q", s[40:48])[0]
    d['real_fsize'] = struct.unpack("<q", s[48:56])[0]
    d['flags'] = struct.unpack("<d", s[56:64])[0]
    d['nlen'] = struct.unpack("B", s[64])[0]
    d['nspace'] = struct.unpack("B", s[65])[0]

    d['name'] = s[66:66+d['nlen']*2].decode('utf-16-le', errors='replace')
    
    return d

def decodeAttributeList(s, record):
    d = {}
    d['type'] = struct.unpack("<I", s[:4])[0]
    d['len'] = struct.unpack("<H", s[4:6])[0]
    d['nlen'] = struct.unpack("B", s[6])[0]
    d['f1'] = struct.unpack("B", s[7])[0]
    d['start_vcn'] = struct.unpack("<d", s[8:16])[0]
    d['file_ref'] = struct.unpack("<Lxx", s[16:22])[0]
    d['seq'] = struct.unpack("<H", s[22:24])[0]
    d['id'] = struct.unpack("<H", s[24:26])[0]
    d['name'] = s[26:26+d['nlen']*2].decode('utf-16-le', errors='replace')
    return d

def decodeVolumeInfo(s, options):
    d = {}
    d['f1'] = struct.unpack("<d", s[:8])[0]
    d['maj_ver'] = struct.unpack("B", s[8])[0]
    d['min_ver'] = struct.unpack("B", s[9])[0]
    d['flags'] = struct.unpack("<H", s[10:12])[0]
    d['f2'] = struct.unpack("<I", s[12:16])[0]

    if options.debug:
        print(f"+Volume Info")
        print(f"++F1: {d['f1']}")
        print(f"++Major Version: {d['maj_ver']}")
        print(f"++Minor Version: {d['min_ver']}")
        print(f"++Flags: {d['flags']}")
        print(f"++F2: {d['f2']}")

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