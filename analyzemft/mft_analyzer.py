#!/usr/bin/env python

# Version 2.1.1
# Author: Benjamin Cance (bjc@tdx.li)
# Copyright Benjamin Cance 2024
import logging
import struct
from typing import Dict, Any, BinaryIO
from .mft_utils import WindowsTime, decodeMFTmagic, decodeMFTisactive, decodeMFTrecordtype, decodeVolumeInfo, decodeObjectID

class MFTAnalyzer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mft: Dict[int, Dict[str, Any]] = {}
        self.folders: Dict[str, str] = {}
        self.num_records: int = 0
        self.logger = logging.getLogger(__name__)
        self.debug = config.get('debug', False)

    def process_mft_file(self, file_mft: BinaryIO):
        self.num_records = 0
        while True:
            raw_record = file_mft.read(1024)
            if not raw_record:
                break
            try:
                record = self.parse_record(raw_record)
                self.mft[self.num_records] = record
                self.num_records += 1
                if self.num_records % 1000 == 0:
                    self.logger.info(f"Processed {self.num_records} records")
            except Exception as e:
                self.logger.error(f"Error processing record {self.num_records}: {e}")

        self.gen_filepaths()

    def parse_record(self, raw_record: bytes) -> Dict[str, Any]:
        record = {'filename': '', 'notes': '', 'fncnt': 0}
        self.decode_mft_header(record, raw_record)

        if record['magic'] == 0x44414142:
            if self.debug:
                self.logger.debug("BAAD MFT Record")
            record['baad'] = True
            return record

        if record['magic'] != 0x454c4946:
            if self.debug:
                self.logger.debug("Corrupt MFT Record")
            record['corrupt'] = True
            return record

        self.parse_attributes(record, raw_record)
        return record

    def decode_mft_header(self, record: Dict[str, Any], raw_record: bytes):
        header_format = "<IHHQHHHHIIQHH"
        header_size = struct.calcsize(header_format)
        header_fields = struct.unpack(header_format, raw_record[:header_size])
        
        field_names = ['magic', 'upd_off', 'upd_cnt', 'lsn', 'seq', 'link', 'attr_off', 'flags', 'size', 'alloc_sizef', 'base_ref', 'next_attrid', 'f1']
        record.update(dict(zip(field_names, header_fields)))
        
        record['recordnum'] = struct.unpack("<I", raw_record[44:48])[0]

        if record['base_ref'] & 0x8000000000000000:
            record['base_ref'] = -(~record['base_ref'] & 0xFFFFFFFFFFFFFFFF) - 1


    def parse_attributes(self, record: Dict[str, Any], raw_record: bytes):
        read_ptr = record['attr_off']
        while read_ptr < 1024:
            attr_record = self.decode_attribute_header(raw_record[read_ptr:])
            if attr_record['type'] == 0xffffffff:
                break

            self.process_attribute(attr_record, raw_record[read_ptr:], record)

            if attr_record['len'] > 0:
                read_ptr += attr_record['len']
            else:
                self.logger.debug("attr_record->len <= 0, exiting loop")
                break

    def decode_attribute_header(self, s: bytes) -> Dict[str, Any]:
        d = {}
        d['type'] = struct.unpack("<L", s[:4])[0]
        if d['type'] == 0xffffffff:
            return d
        
        attr_format = "<LBBHHHHLLQHHLLQQQQ"
        attr_size = struct.calcsize(attr_format)
        attr_fields = struct.unpack(attr_format, s[:attr_size])
        
        field_names = ['len', 'res', 'nlen', 'name_off', 'flags', 'id', 'ssize', 'soff', 'idxflag', 'start_vcn', 'last_vcn', 'run_off', 'compusize', 'f1', 'alen', 'ssize', 'initsize']
        d.update(dict(zip(field_names, attr_fields[1:])))  # Skip 'type' as it's already set

        return d

    def process_attribute(self, attr_record: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]):
        attribute_handlers = {
            0x10: self.handle_standard_information,
            0x20: self.handle_attribute_list,
            0x30: self.handle_file_name,
            0x40: self.handle_object_id,
            0x50: self.handle_security_descriptor,
            0x60: self.handle_volume_name,
            0x70: self.handle_volume_information,
            0x80: self.handle_data,
            0x90: self.handle_index_root,
            0xA0: self.handle_index_allocation,
            0xB0: self.handle_bitmap,
            0xC0: self.handle_reparse_point,
            0xD0: self.handle_ea_information,
            0xE0: self.handle_ea,
            0xF0: self.handle_property_set,
            0x100: self.handle_logged_utility_stream,
        }

        attr_type = attr_record['type']
        handler = attribute_handlers.get(attr_type)

        if handler:
            handler(attr_record, raw_record, record)
        else:
            self.handle_unknown_attribute(attr_record, raw_record, record)

    def handle_unknown_attribute(self, attr_record: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]):
        attr_type = attr_record['type']
        self.logger.warning(f"Unknown attribute type: 0x{attr_type:X} in record {record.get('recordnum', 'Unknown')}")
        self.logger.debug(f"Attribute record: {attr_record}")
        self.logger.debug(f"Raw record (first 64 bytes): {raw_record[:64].hex()}")
        
        # You might want to add this unknown attribute to the record for further analysis
        if 'unknown_attributes' not in record:
            record['unknown_attributes'] = []
        record['unknown_attributes'].append(attr_type)
    
    def decodeMFTHeader(self, record: Dict[str, Any], raw_record: bytes) -> None:
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
        record['f1'] = raw_record[42:44]  
        record['recordnum'] = struct.unpack("<I", raw_record[44:48])[0]

        if record['base_ref'] & 0x8000000000000000:
            record['base_ref'] = -(~record['base_ref'] & 0xFFFFFFFFFFFFFFFF) - 1   

        
    def decodeATRHeader(self, s: bytes) -> Dict[str, Any]:

        d = {}

        d['type'] = struct.unpack("<L",s[:4])[0]

        if d['type'] == 0xffffffff:
            return d
        
        d['len']      = struct.unpack("<L",s[4:8])[0]
        d['res']      = struct.unpack( "B",s[8])[0]
        d['nlen']     = struct.unpack( "B",s[9])[0]
        d['name_off'] = struct.unpack("<H",s[10:12])[0]
        d['flags']    = struct.unpack("<H",s[12:14])[0]
        d['id']       = struct.unpack("<H",s[14:16])[0]

        if d['res'] == 0:
            d['ssize']   = struct.unpack("<L",s[16:20])[0]
            d['soff']    = struct.unpack("<H",s[20:22])[0]
            d['idxflag'] = struct.unpack("<H",s[22:24])[0]

        else:
            d['start_vcn'] = struct.unpack("<d",s[16:24])[0]
            d['last_vcn']  = struct.unpack("<d",s[24:32])[0]
            d['run_off']   = struct.unpack("<H",s[32:34])[0]
            d['compusize'] = struct.unpack("<H",s[34:36])[0]
            d['f1']        = struct.unpack("<I",s[36:40])[0]
            d['alen']      = struct.unpack("<d",s[40:48])[0]
            d['ssize']     = struct.unpack("<d",s[48:56])[0]
            d['initsize']  = struct.unpack("<d",s[56:64])[0]

        return d
    
    def handle_standard_information(self, ATRrecord: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]) -> None:
        if self.config.get('debug', False):
            print(f"Standard Information:\n++Type: {hex(ATRrecord['type'])} Length: {ATRrecord['len']} Resident: {ATRrecord['res']} Name Len: {ATRrecord['nlen']} Name Offset: {ATRrecord['name_off']}")
        SIrecord = self.decodeSIAttribute(raw_record[ATRrecord['soff']:])
        record['si'] = SIrecord
        if self.config.get('debug', False):
            print(f"++CRTime: {SIrecord['crtime'].dtstr}\n++MTime: {SIrecord['mtime'].dtstr}\n++ATime: {SIrecord['atime'].dtstr}\n++EntryTime: {SIrecord['ctime'].dtstr}")

    def handle_attribute_list(self, ATRrecord: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]) -> None:
        if self.config.get('debug', False):
            print("Attribute list")
        if ATRrecord['res'] == 0:
            ALrecord = self.decodeAttributeList(raw_record[ATRrecord['soff']:], record)
            record['al'] = ALrecord
            if self.config.get('debug', False):
                print(f"Name: {ALrecord['name']}")
        else:
            if self.config.get('debug', False):
                print("Non-resident Attribute List?")
            record['al'] = None

    def handle_file_name(self, ATRrecord: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]) -> None:
        if self.config.get('debug', False):
            print("File name record")
        FNrecord = self.decodeFNAttribute(raw_record[ATRrecord['soff']:], record)
        record[('fn', record['fncnt'])] = FNrecord
        if self.config.get('debug', False):
            print(f"Name: {FNrecord['name']} ({record['fncnt']})")
        record['fncnt'] += 1
        if FNrecord['crtime'] != 0:
            if self.config.get('debug', False):
                print(f"\tCRTime: {FNrecord['crtime'].dtstr} MTime: {FNrecord['mtime'].dtstr} ATime: {FNrecord['atime'].dtstr} EntryTime: {FNrecord['ctime'].dtstr}")

    def handle_object_id(self, ATRrecord: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]) -> None:
        ObjectIDRecord = self.decodeObjectID(raw_record[ATRrecord['soff']:])
        record['objid'] = ObjectIDRecord
        if self.config.get('debug', False):
            print("Object ID")

    def handle_security_descriptor(self, ATRrecord: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]) -> None:
        record['sd'] = True
        if self.config.get('debug', False):
            print("Security descriptor")

    def handle_volume_name(self, ATRrecord: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]) -> None:
        record['volname'] = True
        if self.config.get('debug', False):
            print("Volume name")

    def handle_volume_information(self, ATRrecord: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]) -> None:
        if self.config.get('debug', False):
            print("Volume info attribute")
        VolumeInfoRecord = self.decodeVolumeInfo(raw_record[ATRrecord['soff']:])
        record['volinfo'] = VolumeInfoRecord

    def handle_data(self, ATRrecord: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]) -> None:
        record['data'] = True
        if self.config.get('debug', False):
            print("Data attribute")

    def handle_index_root(self, ATRrecord: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]) -> None:
        record['indexroot'] = True
        if self.config.get('debug', False):
            print("Index root")

    def handle_index_allocation(self, ATRrecord: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]) -> None:
        record['indexallocation'] = True
        if self.config.get('debug', False):
            print("Index allocation")

    def handle_bitmap(self, ATRrecord: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]) -> None:
        record['bitmap'] = True
        if self.config.get('debug', False):
            print("Bitmap")

    def handle_reparse_point(self, ATRrecord: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]) -> None:
        record['reparsepoint'] = True
        if self.config.get('debug', False):
            print("Reparse point")

    def handle_ea_information(self, ATRrecord: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]) -> None:
        record['eainfo'] = True
        if self.config.get('debug', False):
            print("EA Information")

    def handle_ea(self, ATRrecord: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]) -> None:
        record['ea'] = True
        if self.config.get('debug', False):
            print("EA")

    def handle_property_set(self, ATRrecord: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]) -> None:
        record['propertyset'] = True
        if self.config.get('debug', False):
            print("Property set")

    def handle_logged_utility_stream(self, ATRrecord: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]) -> None:
        record['loggedutility'] = True
        if self.config.get('debug', False):
            print("Logged utility stream")

    def handle_unknown_attribute(self, ATRrecord: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]) -> None:
        if self.config.get('debug', False):
            print(f"Found an unknown attribute type: {ATRrecord['type']:x}")

    
    def decodeSIAttribute(self, s: bytes) -> Dict[str, Any]:
        d = {}
        d['crtime'] = WindowsTime(struct.unpack("<L", s[:4])[0], struct.unpack("<L", s[4:8])[0], self.config.localtz)
        d['mtime'] = WindowsTime(struct.unpack("<L", s[8:12])[0], struct.unpack("<L", s[12:16])[0], self.config.localtz)
        d['ctime'] = WindowsTime(struct.unpack("<L", s[16:20])[0], struct.unpack("<L", s[20:24])[0], self.config.localtz)
        d['atime'] = WindowsTime(struct.unpack("<L", s[24:28])[0], struct.unpack("<L", s[28:32])[0], self.config.localtz)
        d['dos'] = struct.unpack("<I", s[32:36])[0]
        d['maxver'] = struct.unpack("<I", s[36:40])[0]
        d['ver'] = struct.unpack("<I", s[40:44])[0]
        d['class_id'] = struct.unpack("<I", s[44:48])[0]
        d['own_id'] = struct.unpack("<I", s[48:52])[0]
        d['sec_id'] = struct.unpack("<I", s[52:56])[0]
        d['quota'] = struct.unpack("<d", s[56:64])[0]
        d['usn'] = struct.unpack("<d", s[64:72])[0]
        return d

    def decodeFNAttribute(self, s: bytes, record: Dict[str, Any]) -> Dict[str, Any]:
        d = {}
        d['par_ref'] = struct.unpack("<Lxx", s[:6])[0]
        d['par_seq'] = struct.unpack("<H", s[6:8])[0]
        d['crtime'] = WindowsTime(struct.unpack("<L", s[8:12])[0], struct.unpack("<L", s[12:16])[0], self.config.localtz)
        d['mtime'] = WindowsTime(struct.unpack("<L", s[16:20])[0], struct.unpack("<L", s[20:24])[0], self.config.localtz)
        d['ctime'] = WindowsTime(struct.unpack("<L", s[24:28])[0], struct.unpack("<L", s[28:32])[0], self.config.localtz)
        d['atime'] = WindowsTime(struct.unpack("<L", s[32:36])[0], struct.unpack("<L", s[36:40])[0], self.config.localtz)
        d['alloc_fsize'] = struct.unpack("<q", s[40:48])[0]
        d['real_fsize'] = struct.unpack("<q", s[48:56])[0]
        d['flags'] = struct.unpack("<d", s[56:64])[0]
        d['nlen'] = struct.unpack("B", s[64])[0]
        d['nspace'] = struct.unpack("B", s[65])[0]

        d['name'] = self.decode_unicode(s[66:], d['nlen'])

        if any(ord(c) > 127 for c in d['name']):
            self.add_note(record, 'Filename contains non-ASCII characters')

        return d

    def decodeAttributeList(self, s: bytes, record: Dict[str, Any]) -> Dict[str, Any]:
        d = {}
        d['type'] = struct.unpack("<I", s[:4])[0]
        d['len'] = struct.unpack("<H", s[4:6])[0]
        d['nlen'] = struct.unpack("B", s[6])[0]
        d['f1'] = struct.unpack("B", s[7])[0]
        d['start_vcn'] = struct.unpack("<d", s[8:16])[0]
        d['file_ref'] = struct.unpack("<Lxx", s[16:22])[0]
        d['seq'] = struct.unpack("<H", s[22:24])[0]
        d['id'] = struct.unpack("<H", s[24:26])[0]

        d['name'] = self.decode_unicode(s[26:], d['nlen'])

        if any(ord(c) > 127 for c in d['name']):
            self.add_note(record, 'Attribute name contains non-ASCII characters')

        return d

    def gen_filepaths(self):
        for i in self.mft:
            if self.mft[i]['filename'] == '':
                if self.mft[i]['fncnt'] > 0:
                    self.get_folder_path(i)
                    self.logger.debug(f"Filename (with path): {self.mft[i]['filename']}")
                else:
                    self.mft[i]['filename'] = 'NoFNRecord'

    def get_folder_path(self, seqnum: int) -> str:
        if self.config.get('debug', False):
            print(f"Building Folder For Record Number ({seqnum})")

        if seqnum not in self.mft:
            return 'Orphan'

        if self.mft[seqnum]['filename'] != '':
            return self.mft[seqnum]['filename']

        try:
            if self.mft[seqnum]['fn', 0]['par_ref'] == 5:
                self.mft[seqnum]['filename'] = '/' + self.mft[seqnum]['fn', self.mft[seqnum]['fncnt']-1]['name']
                return self.mft[seqnum]['filename']
        except:
            self.mft[seqnum]['filename'] = 'NoFNRecord'
            return self.mft[seqnum]['filename']

        if self.mft[seqnum]['fn', 0]['par_ref'] == seqnum:
            if self.config.get('debug', False):
                print(f"Error, self-referential, while trying to determine path for seqnum {seqnum}")
            self.mft[seqnum]['filename'] = 'ORPHAN/' + self.mft[seqnum]['fn', self.mft[seqnum]['fncnt']-1]['name']
            return self.mft[seqnum]['filename']

        parentpath = self.get_folder_path(self.mft[seqnum]['fn', 0]['par_ref'])
        self.mft[seqnum]['filename'] = parentpath + '/' + self.mft[seqnum]['fn', self.mft[seqnum]['fncnt']-1]['name']

        return self.mft[seqnum]['filename']

    def add_note(self, record: Dict[str, Any], note: str):
        if record['notes'] == '':
            record['notes'] = note
        else:
            record['notes'] += f" | {note} |"