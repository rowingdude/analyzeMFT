#!/usr/bin/env python

# Version 2.1.1
# Author: Benjamin Cance (bjc@tdx.li)
# Copyright Benjamin Cance 2024
import logging
import struct
from typing import Dict, Any, BinaryIO, Optional
from .mft_utils import WindowsTime, ObjectID, decodeMFTmagic, decodeMFTisactive, decodeMFTrecordtype, decodeVolumeInfo, decodeObjectID
from .error_handler import error_handler, ParsingError

class MFTAnalyzer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mft: Dict[int, Dict[str, Any]] = {}
        self.folders: Dict[str, str] = {}
        self.num_records: int = 0
        self.logger = logging.getLogger(__name__)
        self.debug = config.get('debug', False)

    @error_handler
    def process_mft_file(self, file_mft: BinaryIO) -> None:
        self.num_records = 0
        while True:
            try:
                raw_record = file_mft.read(1024)
                if not raw_record:
                    break
                if len(raw_record) < 42: 
                    self.logger.warning(f"Incomplete record {self.num_records}: only {len(raw_record)} bytes")
                    self.num_records += 1
                    continue

                record = self.parse_record(raw_record)
                self.mft[self.num_records] = record
                self.num_records += 1
                if self.num_records % 1000 == 0:
                    self.logger.info(f"Processed {self.num_records} records")

            except Exception as e:
                self.logger.error(f"Error processing record {self.num_records}: {e}")
                self.num_records += 1

    @error_handler
    def parse_record(self, raw_record: bytes) -> Dict[str, Any]:
        record = {'filename': '', 'notes': '', 'fncnt': 0}
        try:
            if len(raw_record) < 42:
                raise ValueError(f"Record too short: {len(raw_record)} bytes")

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

        except struct.error as e:
            self.logger.warning(f"Struct unpack error in record {self.num_records}: {e}")
            record['corrupt'] = True
        except Exception as e:
            self.logger.error(f"Error parsing record {self.num_records}: {e}")
            record['corrupt'] = True

        return record

    @error_handler
    def decode_mft_header(self, record: Dict[str, Any], raw_record: bytes) -> None:
        header_format = "<IHHQHHHHIIQHH"
        header_size = struct.calcsize(header_format)
        
        if len(raw_record) < header_size:
            raise ParsingError(f"MFT header too short: expected {header_size}, got {len(raw_record)}")
        
        header_fields = struct.unpack(header_format, raw_record[:header_size])
        
        field_names = ['magic', 'upd_off', 'upd_cnt', 'lsn', 'seq', 'link', 'attr_off', 'flags', 'size', 'alloc_sizef', 'base_ref', 'next_attrid', 'f1']
        record.update(dict(zip(field_names, header_fields)))
        
        if len(raw_record) >= 48:
            record['recordnum'] = struct.unpack("<I", raw_record[44:48])[0]
        else:
            self.logger.warning(f"Record too short to read recordnum: {len(raw_record)} bytes")
            record['recordnum'] = None

        if record['base_ref'] & 0x8000000000000000:
            record['base_ref'] = -(~record['base_ref'] & 0xFFFFFFFFFFFFFFFF) - 1

    @error_handler
    def parse_attributes(self, record: Dict[str, Any], raw_record: bytes) -> None:
        read_ptr = record['attr_off']
        while read_ptr < 1024:
            try:
                attr_record = self.decode_attribute_header(raw_record[read_ptr:])
                if attr_record['type'] == 0xffffffff:
                    break

                self.process_attribute(attr_record, raw_record[read_ptr:], record)

                if attr_record['len'] > 0:
                    read_ptr += attr_record['len']
                else:
                    self.logger.debug("attr_record->len <= 0, exiting loop")
                    break
            except Exception as e:
                self.logger.error(f"Error parsing attribute at offset {read_ptr}: {e}")
                break

    @error_handler
    def decode_attribute_header(self, s: bytes) -> Dict[str, Any]:
        d = {}
        if len(s) < 4:
            raise ParsingError(f"Attribute header too short: {len(s)} bytes")
        
        d['type'] = struct.unpack("<L", s[:4])[0]
        if d['type'] == 0xffffffff:
            return d
        
        attr_format = "<LBBHHHHLLQHHLLQQQQ"
        attr_size = struct.calcsize(attr_format)
        
        if len(s) < attr_size:
            raise ParsingError(f"Attribute data too short: expected {attr_size}, got {len(s)}")
        
        attr_fields = struct.unpack(attr_format, s[:attr_size])
        
        field_names = ['len', 'res', 'nlen', 'name_off', 'flags', 'id', 'ssize', 'soff', 'idxflag', 'start_vcn', 'last_vcn', 'run_off', 'compusize', 'f1', 'alen', 'ssize', 'initsize']
        d.update(dict(zip(field_names, attr_fields[1:])))  # Skip 'type' as it's already set

        return d

    @error_handler
    def process_attribute(self, attr_record: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]) -> None:
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
        handler = attribute_handlers.get(attr_type, self.handle_unknown_attribute)

        try:
            handler(attr_record, raw_record, record)
        except Exception as e:
            self.logger.error(f"Error processing attribute type 0x{attr_type:X}: {e}")
            record.setdefault('attribute_errors', []).append(f"Error processing attribute type 0x{attr_type:X}: {e}")


    def handle_unknown_attribute(self, attr_record: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]):
        attr_type = attr_record['type']
        self.logger.debug(f"Unknown attribute type: 0x{attr_type:X} in record {record.get('recordnum', 'Unknown')}")
        
        if 'unknown_attributes' not in record:
            record['unknown_attributes'] = []
        record['unknown_attributes'].append({
            'type': attr_type,
            'length': attr_record.get('len', 0),
            'resident': attr_record.get('res', False),
            'name_length': attr_record.get('nlen', 0),
            'name_offset': attr_record.get('name_off', 0),
            'data': raw_record[:min(128, len(raw_record))].hex()
        })

    def handle_standard_information(self, attr_record: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]):
        try:
            si_record = self.decodeSIAttribute(raw_record[attr_record['soff']:])
            record['si'] = si_record
            if self.config.get('debug', False):
                self.logger.debug(f"Standard Information: {si_record}")
        except Exception as e:
            self.logger.error(f"Error decoding Standard Information attribute: {e}")
            record.setdefault('attribute_errors', []).append(f"Error decoding Standard Information attribute: {e}")

    @error_handler
    def handle_attribute_list(self, attr_record: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]) -> None:
        try:
            if attr_record['res'] == 0:
                al_record = self.decodeAttributeList(raw_record[attr_record['soff']:], record)
                record['al'] = al_record
                if self.debug:
                    self.logger.debug(f"Attribute List: {al_record}")
            else:
                self.logger.info("Non-resident Attribute List encountered")
                record['al'] = self.decodeNonResidentAttributeList(attr_record, raw_record)
        except Exception as e:
            self.logger.error(f"Error decoding Attribute List: {e}")
            record.setdefault('attribute_errors', []).append(f"Error decoding Attribute List: {e}")


    @error_handler
    def decodeNonResidentAttributeList(self, attr_record: Dict[str, Any], raw_record: bytes) -> Dict[str, Any]:
        return {
            "type": "non-resident",
            "start_vcn": attr_record.get('start_vcn'),
            "last_vcn": attr_record.get('last_vcn'),
        }

    def handle_file_name(self, attr_record: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]):
        try:
            fn_record = self.decodeFNAttribute(raw_record[attr_record['soff']:], record)
            record[('fn', record['fncnt'])] = fn_record
            if self.config.get('debug', False):
                self.logger.debug(f"File Name ({record['fncnt']}): {fn_record['name']}")
            record['fncnt'] += 1
        except Exception as e:
            self.logger.error(f"Error decoding File Name attribute: {e}")
            record.setdefault('attribute_errors', []).append(f"Error decoding File Name attribute: {e}")

    def handle_object_id(self, attr_record: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]):
        try:
            object_id_record = self.decodeObjectID(raw_record[attr_record['soff']:])
            record['objid'] = object_id_record
            if self.config.get('debug', False):
                self.logger.debug(f"Object ID: {object_id_record}")
        except Exception as e:
            self.logger.error(f"Error decoding Object ID attribute: {e}")
            record.setdefault('attribute_errors', []).append(f"Error decoding Object ID attribute: {e}")

    def handle_security_descriptor(self, attr_record: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]):
        record['sd'] = True
        if self.config.get('debug', False):
            self.logger.debug("Security descriptor present")

    def handle_volume_name(self, attr_record: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]):
        try:
            volume_name = raw_record[attr_record['soff']:attr_record['soff'] + attr_record['ssize']].decode('utf-16-le').rstrip('\x00')
            record['volname'] = volume_name
            if self.config.get('debug', False):
                self.logger.debug(f"Volume name: {volume_name}")
        except Exception as e:
            self.logger.error(f"Error decoding Volume Name attribute: {e}")
            record.setdefault('attribute_errors', []).append(f"Error decoding Volume Name attribute: {e}")

    def handle_volume_information(self, attr_record: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]):
        try:
            volume_info_record = self.decodeVolumeInfo(raw_record[attr_record['soff']:])
            record['volinfo'] = volume_info_record
            if self.config.get('debug', False):
                self.logger.debug(f"Volume info: {volume_info_record}")
        except Exception as e:
            self.logger.error(f"Error decoding Volume Information attribute: {e}")
            record.setdefault('attribute_errors', []).append(f"Error decoding Volume Information attribute: {e}")

    def handle_data(self, attr_record: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]):
        record['data'] = True
        record['data_size'] = attr_record['ssize'] if attr_record['res'] == 0 else attr_record['alen']
        if self.config.get('debug', False):
            self.logger.debug(f"Data attribute present, size: {record['data_size']}")

    def handle_index_root(self, attr_record: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]):
        record['indexroot'] = True
        if self.config.get('debug', False):
            self.logger.debug("Index root present")

    def handle_index_allocation(self, attr_record: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]):
        record['indexallocation'] = True
        if self.config.get('debug', False):
            self.logger.debug("Index allocation present")

    def handle_bitmap(self, attr_record: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]):
        record['bitmap'] = True
        if self.config.get('debug', False):
            self.logger.debug("Bitmap present")

    def handle_reparse_point(self, attr_record: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]):
        try:
            reparse_data = raw_record[attr_record['soff']:attr_record['soff'] + attr_record['ssize']]
            reparse_info = {
                'size': len(reparse_data),
                'data': reparse_data.hex()
            }

            if len(reparse_data) >= 4:
                reparse_info['type'] = struct.unpack("<I", reparse_data[:4])[0]
            
            if len(reparse_data) >= 8:
                reparse_info['flags'] = struct.unpack("<H", reparse_data[4:6])[0]
                reparse_info['data_length'] = struct.unpack("<H", reparse_data[6:8])[0]
            
            if len(reparse_data) > 8:
                reparse_info['data_buffer'] = reparse_data[8:].hex()

            record['reparsepoint'] = reparse_info

            if self.config.get('debug', False):
                self.logger.debug(f"Reparse point present, size: {reparse_info['size']} bytes")
                if 'type' in reparse_info:
                    self.logger.debug(f"Reparse point type: 0x{reparse_info['type']:X}")

        except Exception as e:
            self.logger.error(f"Error decoding Reparse Point attribute: {e}")
            record.setdefault('attribute_errors', []).append(f"Error decoding Reparse Point attribute: {e}")

    def handle_ea_information(self, attr_record: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]):
        record['eainfo'] = True
        if self.config.get('debug', False):
            self.logger.debug("EA Information present")

    def handle_ea(self, attr_record: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]):
        record['ea'] = True
        if self.config.get('debug', False):
            self.logger.debug("EA present")

    def handle_property_set(self, attr_record: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]):
        record['propertyset'] = True
        if self.config.get('debug', False):
            self.logger.debug("Property set present")

    def handle_logged_utility_stream(self, attr_record: Dict[str, Any], raw_record: bytes, record: Dict[str, Any]):
        record['loggedutility'] = True
        if self.config.get('debug', False):
            self.logger.debug("Logged utility stream present")

    def decodeSIAttribute(self, raw_data: bytes) -> Dict[str, Any]:
        si = {}
        data_len = len(raw_data)
        localtz = self.config.get('localtz', False)

        def unpack_time(offset):
            try:
                if data_len >= offset + 8:
                    return WindowsTime(struct.unpack("<Q", raw_data[offset:offset+8])[0], localtz)
                elif data_len >= offset + 4:
                    low, high = struct.unpack("<LL", raw_data[offset:offset+8])
                    return WindowsTime((high << 32) | low, localtz)
                else:
                    return WindowsTime(0, localtz)
            except struct.error:
                self.logger.warning(f"Error unpacking time at offset {offset}")
                return WindowsTime(0, localtz)

        si['crtime'] = unpack_time(0)
        si['mtime']  = unpack_time(8)
        si['ctime']  = unpack_time(16)
        si['atime']  = unpack_time(24)

        if data_len >= 36:
            si['dos'] = struct.unpack("<I", raw_data[32:36])[0]
        if data_len >= 40:
            si['maxver'] = struct.unpack("<I", raw_data[36:40])[0]
        if data_len >= 44:
            si['ver'] = struct.unpack("<I", raw_data[40:44])[0]
        if data_len >= 48:
            si['class_id'] = struct.unpack("<I", raw_data[44:48])[0]
        if data_len >= 52:
            si['own_id'] = struct.unpack("<I", raw_data[48:52])[0]
        if data_len >= 56:
            si['sec_id'] = struct.unpack("<I", raw_data[52:56])[0]
        if data_len >= 64:
            si['quota'] = struct.unpack("<Q", raw_data[56:64])[0]
        if data_len >= 72:
            si['usn'] = struct.unpack("<Q", raw_data[64:72])[0]

        if self.config.get('debug', False):
            self.logger.debug(f"SI Timestamps: crtime={si['crtime']}, mtime={si['mtime']}, ctime={si['ctime']}, atime={si['atime']}")

        return si

    def decodeAttributeList(self, raw_data: bytes, record: Dict[str, Any]) -> Dict[str, Any]:
        al = {}
        data_len = len(raw_data)
        
        if data_len == 0:
            return {"error": "Empty Attribute List data"}

        if data_len < 4:
            return {"error": f"Attribute List data too short: {data_len} bytes"}

        al['type'] = struct.unpack("<I", raw_data[:4])[0]
        
        if data_len >= 6:
            al['len'] = struct.unpack("<H", raw_data[4:6])[0]
        if data_len >= 7:
            al['nlen'] = struct.unpack("B", raw_data[6:7])[0]
        if data_len >= 8:
            al['f1'] = struct.unpack("B", raw_data[7:8])[0]
        if data_len >= 16:
            al['start_vcn'] = struct.unpack("<Q", raw_data[8:16])[0]
        if data_len >= 24:
            al['file_ref'] = struct.unpack("<Q", raw_data[16:24])[0]
        if data_len >= 26:
            al['seq'] = struct.unpack("<H", raw_data[24:26])[0]
        if data_len >= 28:
            al['id'] = struct.unpack("<H", raw_data[26:28])[0]
        
        if data_len >= 28 and 'nlen' in al:
            name_end = min(28 + al['nlen'] * 2, data_len)
            al['name'] = raw_data[28:name_end].decode('utf-16-le', errors='replace')
        
        return al

    def decodeFNAttribute(self, raw_data: bytes, record: Dict[str, Any]) -> Dict[str, Any]:
        fn = {}
        data_len = len(raw_data)
        localtz = self.config.get('localtz', False)

        def unpack_time(offset):
            try:
                if data_len >= offset + 8:
                    return WindowsTime(struct.unpack("<Q", raw_data[offset:offset+8])[0], localtz)
                elif data_len >= offset + 4:
                    low, high = struct.unpack("<LL", raw_data[offset:offset+8])
                    return WindowsTime((high << 32) | low, localtz)
                else:
                    return WindowsTime(0, localtz)
            except struct.error:
                self.logger.warning(f"Error unpacking time at offset {offset}")
                return WindowsTime(0, localtz)

            if data_len >= 8:
                fn['par_ref'] = struct.unpack("<Q", raw_data[0:8])[0]
            else:
                fn['par_ref'] = 0

        fn['crtime'] = unpack_time(8)
        fn['mtime']  = unpack_time(16)
        fn['ctime']  = unpack_time(24)
        fn['atime']  = unpack_time(32)

        if data_len >= 48:
            fn['alloc_fsize'] = struct.unpack("<Q", raw_data[40:48])[0]
        if data_len >= 56:
            fn['real_fsize'] = struct.unpack("<Q", raw_data[48:56])[0]
        if data_len >= 60:
            fn['flags'] = struct.unpack("<I", raw_data[56:60])[0]
        if data_len >= 64:
            fn['reparse'] = struct.unpack("<I", raw_data[60:64])[0]
        if data_len >= 65:
            fn['nlen'] = struct.unpack("B", raw_data[64:65])[0]
        if data_len >= 66:
            fn['nspace'] = struct.unpack("B", raw_data[65:66])[0]

        name_end = min(66 + fn.get('nlen', 0) * 2, data_len)
        fn['name'] = raw_data[66:name_end].decode('utf-16-le', errors='replace')

        if self.config.get('debug', False):
            self.logger.debug(f"FN Timestamps: crtime={fn['crtime']}, mtime={fn['mtime']}, ctime={fn['ctime']}, atime={fn['atime']}")

        return fn
    def decodeObjectID(self, raw_data: bytes) -> Dict[str, Any]:
        return {
            'objid':      ObjectID(raw_data[ 0:16]),
            'orig_volid': ObjectID(raw_data[16:32]),
            'orig_objid': ObjectID(raw_data[32:48]),
            'orig_domid': ObjectID(raw_data[48:64])
        }

    def decodeVolumeInfo(self, raw_data: bytes) -> Dict[str, Any]:
        vi = {}
        vi['f1']      = struct.unpack("<Q", raw_data[ 0: 8])[0]
        vi['maj_ver'] = struct.unpack("B",  raw_data[ 8: 9])[0]
        vi['min_ver'] = struct.unpack("B",  raw_data[ 9:10])[0]
        vi['flags']   = struct.unpack("<H", raw_data[10:12])[0]
        vi['f2']      = struct.unpack("<I", raw_data[12:16])[0]
        return vi

    def gen_filepaths(self) -> None:
        for i in self.mft:
            if self.mft[i]['filename'] == '':
                if self.mft[i]['fncnt'] > 0:
                    self.get_folder_path(i)
                    self.logger.debug(f"Filename (with path): {self.mft[i]['filename']}")
                else:
                    self.mft[i]['filename'] = 'NoFNRecord'

    @error_handler
    def get_folder_path(self, seqnum: int) -> str:
        if self.debug:
            self.logger.debug(f"Building Folder For Record Number ({seqnum})")

        if seqnum not in self.mft:
            return 'Orphan'

        if self.mft[seqnum]['filename'] != '':
            return self.mft[seqnum]['filename']

        try:
            if self.mft[seqnum]['fn', 0]['par_ref'] == 5:
                self.mft[seqnum]['filename'] = '/' + self.mft[seqnum]['fn', self.mft[seqnum]['fncnt']-1]['name']
                return self.mft[seqnum]['filename']
        except KeyError:
            self.mft[seqnum]['filename'] = 'NoFNRecord'
            return self.mft[seqnum]['filename']

        if self.mft[seqnum]['fn', 0]['par_ref'] == seqnum:
            if self.debug:
                self.logger

    def add_note(self, record: Dict[str, Any], note: str):
        if record['notes'] == '':
            record['notes'] = note
        else:
            record['notes'] += f" | {note} |"