#!/usr/bin/env python

# Version 2.1
#
# Author: Benjamin Cance (bjc@tdx.li)
# Copyright Benjamin Cance 2024
#
# 2-Aug-24 
# - Updating to current PEP

import struct
import binascii
from typing import Dict, Any, List, Union
from argparse import ArgumentParser
from . import mftutils

UNICODE_HACK = True

attribute_handlers = {
    0x10:  handle_standard_information,
    0x20:  handle_attribute_list,
    0x30:  handle_file_name,
    0x40:  handle_object_id,
    0x50:  handle_security_descriptor,
    0x60:  handle_volume_name,
    0x70:  handle_volume_information,
    0x80:  handle_data,
    0x90:  handle_index_root,
    0xA0:  handle_index_allocation,
    0xB0:  handle_bitmap,
    0xC0:  handle_reparse_point,
    0xD0:  handle_ea_information,
    0xE0:  handle_ea,
    0xF0:  handle_property_set,
    0x100: handle_logged_utility_stream,
}

def set_default_options() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("--debug"   , action="store_true", default=False)
    parser.add_argument("--localtz" , default                     =None)
    parser.add_argument("--bodystd" , action="store_true", default=False)
    parser.add_argument("--bodyfull", action="store_true", default=False)
    return parser

def parse_record(raw_record: bytes, options: Any) -> Dict[str, Any]:
    record: Dict[str, Any] = {'filename': '', 'notes': '', 'fncnt': 0}

    decodeMFTHeader(record, raw_record)

    record_number = record['recordnum']

    if options.debug:
        print(f"-->Record number: {record_number}\n\tMagic: {record['magic']} Attribute offset: {record['attr_off']} Flags: {hex(int(record['flags']))} Size:{record['size']}")

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

    while (read_ptr < 1024):

        ATRrecord = decodeATRHeader(raw_record[read_ptr:])
        if ATRrecord['type'] == 0xffffffff:  # End of attributes
            break

        if options.debug:
            print(f"Attribute type: {ATRrecord['type']:x} Length: {ATRrecord['len']} Res: {ATRrecord['res']:x}")

        if ATRrecord['type'] == 0x10:  # Standard Information
            if options.debug:
                print(f"Standard Information:\n++Type: {hex(ATRrecord['type'])} Length: {ATRrecord['len']} Resident: {ATRrecord['res']} Name Len:{ATRrecord['nlen']} Name Offset: {ATRrecord['name_off']}")
            SIrecord = decodeSIAttribute(raw_record[read_ptr+ATRrecord['soff']:], options.localtz)
            record['si'] = SIrecord
            if options.debug:
                print(f"++CRTime: {SIrecord['crtime'].dtstr}\n++MTime: {SIrecord['mtime'].dtstr}\n++ATime: {SIrecord['atime'].dtstr}\n++EntryTime: {SIrecord['ctime'].dtstr}")

        elif ATRrecord['type'] == 0x20:  # Attribute list
            if options.debug:
                print("Attribute list")
            if ATRrecord['res'] == 0:
                ALrecord = decodeAttributeList(raw_record[read_ptr+ATRrecord['soff']:], record)
                record['al'] = ALrecord
                if options.debug:
                    print(f"Name: {ALrecord['name']}")
            else:
                if options.debug:
                    print("Non-resident Attribute List?")
                record['al'] = None


        elif ATRrecord['type'] == 0x30:  # File name
            if options.debug:
                print("File name record")
            FNrecord = decodeFNAttribute(raw_record[read_ptr+ATRrecord['soff']:], options.localtz, record)
            record[('fn', record['fncnt'])] = FNrecord
            if options.debug:
                print(f"Name: {FNrecord['name']} ({record['fncnt']})")
            record['fncnt'] += 1
            if FNrecord['crtime'] != 0:
                if options.debug:
                    print(f"\tCRTime: {FNrecord['crtime'].dtstr} MTime: {FNrecord['mtime'].dtstr} ATime: {FNrecord['atime'].dtstr} EntryTime: {FNrecord['ctime'].dtstr}")

        elif ATRrecord['type'] == 0x40:                 #  Object ID
            ObjectIDRecord = decodeObjectID(raw_record[read_ptr+ATRrecord['soff']:])
            record['objid'] = ObjectIDRecord
            if options.debug: print(f"Object ID")

        elif ATRrecord['type'] == 0x50:                 # Security descriptor
            record['sd'] = True
            if options.debug: print(f"Security descriptor")

        elif ATRrecord['type'] == 0x60:                 # Volume name
            record['volname'] = True
            if options.debug: print(f"Volume name")

        elif ATRrecord['type'] == 0x70:                 # Volume information
            if options.debug: print(f"Volume info attribute")
            VolumeInfoRecord = decodeVolumeInfo(raw_record[read_ptr+ATRrecord['soff']:],options)
            record['volinfo'] = VolumeInfoRecord

        elif ATRrecord['type'] == 0x80:                 # Data
            record['data'] = True
            if options.debug: print(f"Data attribute")

        elif ATRrecord['type'] == 0x90:                 # Index root
            record['indexroot'] = True
            if options.debug: print(f"Index root")

        elif ATRrecord['type'] == 0xA0:                 # Index allocation
            record['indexallocation'] = True
            if options.debug: print(f"Index allocation")

        elif ATRrecord['type'] == 0xB0:                 # Bitmap
            record['bitmap'] = True
            if options.debug: print(f"Bitmap")

        elif ATRrecord['type'] == 0xC0:                 # Reparse point
            record['reparsepoint'] = True
            if options.debug: print(f"Reparse point")

        elif ATRrecord['type'] == 0xD0:                 # EA Information
            record['eainfo'] = True
            if options.debug: print(f"EA Information")

        elif ATRrecord['type'] == 0xE0:                 # EA
            record['ea'] = True
            if options.debug: print(f"EA")

        elif ATRrecord['type'] == 0xF0:                 # Property set
            record['propertyset'] = True
            if options.debug: print(f"Property set")

        elif ATRrecord['type'] == 0x100:                 # Logged utility stream
            record['loggedutility'] = True
            if options.debug: print(f"Logged utility stream")

        else:
            if options.debug: print(f"Found an unknown attribute")

        if ATRrecord['len'] > 0:
            read_ptr = read_ptr + ATRrecord['len']
        else:
            if options.debug: print(f"ATRrecord->len < 0, exiting loop")
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

    tmp_string = ["%d" % record['seq']]
    csv_string.extend(tmp_string)

    if record['fncnt'] > 0:
        csv_string.extend([str(record['fn',0]['par_ref']), str(record['fn',0]['par_seq'])])
    else:
        csv_string.extend(['NoParent', 'NoParent'])

    if record['fncnt'] > 0 and 'si' in record:
        
        filenameBuffer = [record['filename'],  str(record['si']['crtime'].dtstr),
                   record['si']['mtime'].dtstr,    record['si']['atime'].dtstr, record['si']['ctime'].dtstr,
                   record['fn',0]['crtime'].dtstr, record['fn',0]['mtime'].dtstr,
                   record['fn',0]['atime'].dtstr,  record['fn',0]['ctime'].dtstr]
    elif 'si' in record:

        filenameBuffer = ['NoFNRecord', str(record['si']['crtime'].dtstr),
                   record['si']['mtime'].dtstr, record['si']['atime'].dtstr, record['si']['ctime'].dtstr,
                   'NoFNRecord', 'NoFNRecord', 'NoFNRecord','NoFNRecord']
    else:

        filenameBuffer = ['NoFNRecord', 'NoSIRecord', 'NoSIRecord', 'NoSIRecord', 'NoSIRecord',
                          'NoFNRecord', 'NoFNRecord', 'NoFNRecord', 'NoFNRecord']


    csv_string.extend(filenameBuffer)

    if 'objid' in record:
        objidBuffer = [record['objid']['objid'], record['objid']['orig_volid'],
                    record['objid']['orig_objid'], record['objid']['orig_domid']]
    else:
        objidBuffer = ['','','','']

    csv_string.extend(objidBuffer)

    for i in range(1, record['fncnt']):
        filenameBuffer = [record['fn',i]['name'], record['fn',i]['crtime'].dtstr, record['fn',i]['mtime'].dtstr,
                   record['fn',i]['atime'].dtstr, record['fn',i]['ctime'].dtstr]
        csv_string.extend(filenameBuffer)
        filenameBuffer = ''

    if record['fncnt'] < 2:
        tmp_string = ['','','','','','','','','','','','','','','']
    elif record['fncnt'] == 2:
        tmp_string = ['','','','','','','','','','']
    elif record['fncnt'] == 3:
        tmp_string = ['','','','','']

    csv_string.extend(tmp_string)

    
    attributes = ['si', 'al', 'objid', 'volname', 'volinfo', 'data', 'indexroot', 
                'indexallocation', 'bitmap', 'reparse', 'eainfo', 'ea', 
                'propertyset', 'loggedutility']

    csv_string.extend(
        ['True' if attr in record else 'False' for attr in attributes]
    )

    # Special case for 'fncnt'
    csv_string.append('True' if record.get('fncnt', 0) > 0 else 'False')

    if 'notes' in record:                        # Log of abnormal activity related to this record
        csv_string.append(record['notes'])
    else:
        csv_string.append('None')
        record['notes'] = ''

    if 'stf-fn-shift' in record:
        csv_string.append('Y')
    else:
        csv_string.append('N')

    if 'usec-zero' in record:
        csv_string.append('Y')
    else:
        csv_string.append('N')

    return csv_string

# MD5|name|inode|mode_as_string|UID|GID|size|atime|mtime|ctime|crtime
def mft_to_body(record, full, std):
    ' Return a MFT record in bodyfile format'

# Add option to use STD_INFO

    if record['fncnt'] > 0:

        if full == True: # Use full path
            name = record['filename']
        else:
            name = record['fn',0]['name']

        if std == True:     # Use STD_INFO
            rec_bodyfile = ("%s|%s|%s|%s|%s|%s|%s|%d|%d|%d|%d\n" %
                           ('0',name,'0','0','0','0',
                           int(record['fn',0]['real_fsize']),
                           int(record['si']['atime'].unixtime),  # was str ....
                           int(record['si']['mtime'].unixtime),
                           int(record['si']['ctime'].unixtime),
                           int(record['si']['ctime'].unixtime)))
        else:               # Use FN
            rec_bodyfile = ("%s|%s|%s|%s|%s|%s|%s|%d|%d|%d|%d\n" %
                           ('0',name,'0','0','0','0',
                           int(record['fn',0]['real_fsize']),
                           int(record['fn',0]['atime'].unixtime),
                           int(record['fn',0]['mtime'].unixtime),
                           int(record['fn',0]['ctime'].unixtime),
                           int(record['fn',0]['crtime'].unixtime)))

    else:
        if 'si' in record:
            rec_bodyfile = ("%s|%s|%s|%s|%s|%s|%s|%d|%d|%d|%d\n" %
                           ('0','No FN Record','0','0','0','0', '0',
                           int(record['si']['atime'].unixtime),  # was str ....
                           int(record['si']['mtime'].unixtime),
                           int(record['si']['ctime'].unixtime),
                           int(record['si']['ctime'].unixtime)))
        else:
            rec_bodyfile = ("%s|%s|%s|%s|%s|%s|%s|%d|%d|%d|%d\n" %
                                ('0','Corrupt Record','0','0','0','0', '0',0, 0, 0, 0))

    return (rec_bodyfile)


def mft_to_l2t(record):
    ' Return a MFT record in l2t CSV output format'

    if record['fncnt'] > 0:
        for i in ('atime', 'mtime', 'ctime', 'crtime'):
            (date,time) = record['fn',0][i].dtstr.split(' ')

            if i == 'atime':
                type_str = '$FN [.A..] time'
                macb_str = '.A..'
            if i == 'mtime':
                type_str = '$FN [M...] time'
                macb_str = 'M...'
            if i == 'ctime':
                type_str = '$FN [..C.] time'
                macb_str = '..C.'
            if i == 'crtime':
                type_str = '$FN [...B] time'
                macb_str = '...B'

            csv_string = ("%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s\n" %
                 (date, time, 'TZ', macb_str, 'FILE', 'NTFS $MFT', type_str, 'user', 'host', record['filename'], 'desc',
                  'version', record['filename'], record['seq'], record['notes'], 'format', 'extra'))

    elif 'si' in record:
        for i in ('atime', 'mtime', 'ctime', 'crtime'):
            (date,time) = record['si'][i].dtstr.split(' ')

            if i == 'atime':
                type_str = '$SI [.A..] time'
                macb_str = '.A..'
            if i == 'mtime':
                type_str = '$SI [M...] time'
                macb_str = 'M...'
            if i == 'ctime':
                type_str = '$SI [..C.] time'
                macb_str = '..C.'
            if i == 'crtime':
                type_str = '$SI [...B] time'
                macb_str = '...B'

            csv_string = ("%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s\n" %
                 (date, time, 'TZ', macb_str, 'FILE', 'NTFS $MFT', type_str, 'user', 'host', record['filename'], 'desc',
                  'version', record['filename'], record['seq'], record['notes'], 'format', 'extra'))

    else:
        csv_string = ("%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s\n" %
                  ('-', '-', 'TZ', 'unknown time', 'FILE', 'NTFS $MFT', 'unknown time', 'user', 'host', 'Corrupt Record', 'desc',
                  'version', 'NoFNRecord', record['seq'], '-', 'format', 'extra'))

    return csv_string


def add_note(record, s):
    if  record['notes'] == '':
        record['notes'] = "%s" % s
    else:
        record['notes'] = f"{record['notes']} | {s} |"


def decodeMFTHeader(record: Dict[str, Any], raw_record: bytes) -> None:
    record['magic'] = struct.unpack("<I", raw_record[:4])[0]
    record['upd_off'] = struct.unpack("<H", raw_record[4:6])[0]
    record['upd_cnt'] = struct.unpack("<H", raw_record[6:8])[0]
    record['lsn'] = struct.unpack("<q", raw_record[8:16])[0] 
    record['seq'] = struct.unpack("<H", raw_record[16:18])[0]
    record['link'] = struct.unpack("<H", raw_record[18:20])[0]
    record['attr_off'] = struct.unpack("<H", raw_record[20:22])[0]
    record['flags'] = struct.unpack("<H", raw_record[22:24])[0]
    record['size'] = struct.unpack("<I", raw_record[24:28])[0]
    record['alloc_sizef'] = struct.unpack("<I", raw_record[28:32])[0]
    record['base_ref'] = struct.unpack("<q", raw_record[32:40])[0] 
    record['next_attrid'] = struct.unpack("<H", raw_record[40:42])[0]
    record['f1'] = raw_record[42:44]  # Padding
    record['recordnum'] = struct.unpack("<I", raw_record[44:48])[0]

    # Convert unsigned integers to signed if necessary
    if record['base_ref'] & 0x8000000000000000:
        record['base_ref'] = -(~record['base_ref'] & 0xFFFFFFFFFFFFFFFF) - 1                        


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
    d['type'] = struct.unpack("<L",s[:4])[0]
    if d['type'] == 0xffffffff:
        return d
    d['len'] = struct.unpack("<L",s[4:8])[0]
    d['res'] = struct.unpack("B",s[8])[0]
    d['nlen'] = struct.unpack("B",s[9])[0]                  # This name is the name of the ADS, I think.
    d['name_off'] = struct.unpack("<H",s[10:12])[0]
    d['flags'] = struct.unpack("<H",s[12:14])[0]
    d['id'] = struct.unpack("<H",s[14:16])[0]
    if d['res'] == 0:
        d['ssize'] = struct.unpack("<L",s[16:20])[0]
        d['soff'] = struct.unpack("<H",s[20:22])[0]
        d['idxflag'] = struct.unpack("<H",s[22:24])[0]
    else:
        d['start_vcn'] = struct.unpack("<d",s[16:24])[0]
        d['last_vcn'] = struct.unpack("<d",s[24:32])[0]
        d['run_off'] = struct.unpack("<H",s[32:34])[0]
        d['compusize'] = struct.unpack("<H",s[34:36])[0]
        d['f1'] = struct.unpack("<I",s[36:40])[0]
        d['alen'] = struct.unpack("<d",s[40:48])[0]
        d['ssize'] = struct.unpack("<d",s[48:56])[0]
        d['initsize'] = struct.unpack("<d",s[56:64])[0]

    return d

def decodeSIAttribute(s, localtz):

    d = {}
    d['crtime'] = mftutils.WindowsTime(struct.unpack("<L",s[:4])[0],struct.unpack("<L",s[4:8])[0],localtz)
    d['mtime'] = mftutils.WindowsTime(struct.unpack("<L",s[8:12])[0],struct.unpack("<L",s[12:16])[0],localtz)
    d['ctime'] = mftutils.WindowsTime(struct.unpack("<L",s[16:20])[0],struct.unpack("<L",s[20:24])[0],localtz)
    d['atime'] = mftutils.WindowsTime(struct.unpack("<L",s[24:28])[0],struct.unpack("<L",s[28:32])[0],localtz)
    d['dos'] = struct.unpack("<I",s[32:36])[0]          # 4
    d['maxver'] = struct.unpack("<I",s[36:40])[0]       # 4
    d['ver'] = struct.unpack("<I",s[40:44])[0]          # 4
    d['class_id'] = struct.unpack("<I",s[44:48])[0]     # 4
    d['own_id'] = struct.unpack("<I",s[48:52])[0]       # 4
    d['sec_id'] = struct.unpack("<I",s[52:56])[0]       # 4
    d['quota'] = struct.unpack("<d",s[56:64])[0]        # 8
    d['usn'] = struct.unpack("<d",s[64:72])[0]          # 8 - end of date to here is 40

    return d

def decodeFNAttribute(s, localtz, record):

    hexFlag = False
    # File name attributes can have null dates.

    d = {}
    d['par_ref'] = struct.unpack("<Lxx", s[:6])[0]      # Parent reference nummber + seq number = 8 byte "File reference to the parent directory.")
    d['par_seq'] = struct.unpack("<H",s[6:8])[0]        # Parent sequence number
    d['crtime'] = mftutils.WindowsTime(struct.unpack("<L",s[8:12])[0],struct.unpack("<L",s[12:16])[0],localtz)
    d['mtime'] = mftutils.WindowsTime(struct.unpack("<L",s[16:20])[0],struct.unpack("<L",s[20:24])[0],localtz)
    d['ctime'] = mftutils.WindowsTime(struct.unpack("<L",s[24:28])[0],struct.unpack("<L",s[28:32])[0],localtz)
    d['atime'] = mftutils.WindowsTime(struct.unpack("<L",s[32:36])[0],struct.unpack("<L",s[36:40])[0],localtz)
    d['alloc_fsize'] = struct.unpack("<q",s[40:48])[0]
    d['real_fsize'] = struct.unpack("<q",s[48:56])[0]
    d['flags'] = struct.unpack("<d",s[56:64])[0]            # 0x01=NTFS, 0x02=DOS
    d['nlen'] = struct.unpack("B",s[64])[0]
    d['nspace'] = struct.unpack("B",s[65])[0]

    if UNICODE_HACK:
        d['name'] = ''
        for i in range(66, 66 + d['nlen']*2):
            if s[i] != '\x00':                         # Just skip over nulls
                if s[i] > '\x1F' and s[i] < '\x80':          # If it is printable, add it to the string
                    d['name'] = d['name'] + s[i]
                else:
                    d['name'] = "%s0x%02s" % (d['name'], s[i].encode("hex"))
                    hexFlag = True

    else:
        d['name'] = s[66:66+d['nlen']*2]

    if hexFlag:
        add_note(record, 'Filename - chars converted to hex')

    return d

def decodeAttributeList(s, record):

    hexFlag = False

    d = {}
    d['type'] = struct.unpack("<I",s[:4])[0]                # 4
    d['len'] = struct.unpack("<H",s[4:6])[0]                # 2
    d['nlen'] = struct.unpack("B",s[6])[0]                  # 1
    d['f1'] = struct.unpack("B",s[7])[0]                    # 1
    d['start_vcn'] = struct.unpack("<d",s[8:16])[0]         # 8
    d['file_ref'] = struct.unpack("<Lxx",s[16:22])[0]       # 6
    d['seq'] = struct.unpack("<H",s[22:24])[0]              # 2
    d['id'] = struct.unpack("<H",s[24:26])[0]               # 4
    if (UNICODE_HACK):
        d['name'] = ''
        for i in range(26, 26 + d['nlen']*2):
            if s[i] != '\x00':                         # Just skip over nulls
                if s[i] > '\x1F' and s[i] < '\x80':          # If it is printable, add it to the string
                    d['name'] = d['name'] + s[i]
                else:
                    d['name'] = "%s0x%02s" % (d['name'], s[i].encode("hex"))
                    hexFlag = True
    else:
        d['name'] = s[26:26+d['nlen']*2]

    if hexFlag:
        add_note(record, 'Filename - chars converted to hex')

    return d

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

def handle_standard_information(ATRrecord, raw_record, record, options):
    if options.debug:
        print(f"Standard Information:\n++Type: {hex(ATRrecord['type'])} Length: {ATRrecord['len']} Resident: {ATRrecord['res']} Name Len: {ATRrecord['nlen']} Name Offset: {ATRrecord['name_off']}")
    SIrecord = decodeSIAttribute(raw_record[ATRrecord['soff']:], options.localtz)
    record['si'] = SIrecord
    if options.debug:
        print(f"++CRTime: {SIrecord['crtime'].dtstr}\n++MTime: {SIrecord['mtime'].dtstr}\n++ATime: {SIrecord['atime'].dtstr}\n++EntryTime: {SIrecord['ctime'].dtstr}")

def handle_attribute_list(ATRrecord, raw_record, record, options):
    if options.debug:
        print("Attribute list")
    if ATRrecord['res'] == 0:
        ALrecord = decodeAttributeList(raw_record[ATRrecord['soff']:], record)
        record['al'] = ALrecord
        if options.debug:
            print(f"Name: {ALrecord['name']}")
    else:
        if options.debug:
            print("Non-resident Attribute List?")
        record['al'] = None

def handle_file_name(ATRrecord, raw_record, record, options):
    if options.debug:
        print("File name record")
    FNrecord = decodeFNAttribute(raw_record[ATRrecord['soff']:], options.localtz, record)
    record[('fn', record['fncnt'])] = FNrecord
    if options.debug:
        print(f"Name: {FNrecord['name']} ({record['fncnt']})")
    record['fncnt'] += 1
    if FNrecord['crtime'] != 0:
        if options.debug:
            print(f"\tCRTime: {FNrecord['crtime'].dtstr} MTime: {FNrecord['mtime'].dtstr} ATime: {FNrecord['atime'].dtstr} EntryTime: {FNrecord['ctime'].dtstr}")

def handle_object_id(ATRrecord, raw_record, record, options):
    ObjectIDRecord = decodeObjectID(raw_record[ATRrecord['soff']:])
    record['objid'] = ObjectIDRecord
    if options.debug:
        print("Object ID")

def handle_security_descriptor(ATRrecord, raw_record, record, options):
    record['sd'] = True
    if options.debug:
        print("Security descriptor")

def handle_volume_name(ATRrecord, raw_record, record, options):
    record['volname'] = True
    if options.debug:
        print("Volume name")

def handle_volume_information(ATRrecord, raw_record, record, options):
    if options.debug:
        print("Volume info attribute")
    VolumeInfoRecord = decodeVolumeInfo(raw_record[ATRrecord['soff']:], options)
    record['volinfo'] = VolumeInfoRecord

def handle_data(ATRrecord, raw_record, record, options):
    record['data'] = True
    if options.debug:
        print("Data attribute")

def handle_index_root(ATRrecord, raw_record, record, options):
    record['indexroot'] = True
    if options.debug:
        print("Index root")

def handle_index_allocation(ATRrecord, raw_record, record, options):
    record['indexallocation'] = True
    if options.debug:
        print("Index allocation")

def handle_bitmap(ATRrecord, raw_record, record, options):
    record['bitmap'] = True
    if options.debug:
        print("Bitmap")

def handle_reparse_point(ATRrecord, raw_record, record, options):
    record['reparsepoint'] = True
    if options.debug:
        print("Reparse point")

def handle_ea_information(ATRrecord, raw_record, record, options):
    record['eainfo'] = True
    if options.debug:
        print("EA Information")

def handle_ea(ATRrecord, raw_record, record, options):
    record['ea'] = True
    if options.debug:
        print("EA")

def handle_property_set(ATRrecord, raw_record, record, options):
    record['propertyset'] = True
    if options.debug:
        print("Property set")

def handle_logged_utility_stream(ATRrecord, raw_record, record, options):
    record['loggedutility'] = True
    if options.debug:
        print("Logged utility stream")

def handle_unknown_attribute(ATRrecord, raw_record, record, options):
    if options.debug:
        print(f"Found an unknown attribute type: {ATRrecord['type']:x}")