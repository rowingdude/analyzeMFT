import struct
import uuid
import hashlib
import zlib
import logging
import traceback
from typing import Dict, Set, List, Optional, Any, Union

from .constants import *
from .windows_time import WindowsTime
from .validators import validate_attribute_length, ValidationError


class MftRecord:
    
    def __init__(self, raw_record: bytes, compute_hashes: bool = False, debug_level: int = 0, logger=None):
        
        if len(raw_record) < MFT_RECORD_SIZE:
            raise ValueError(f"MFT record too short: {len(raw_record)} bytes, expected {MFT_RECORD_SIZE}")

        self.raw_record = raw_record
        self.debug_level = debug_level
        self.logger = logger or logging.getLogger('analyzeMFT.mft_record')
        
        self.magic = 0
        self.upd_off = 0
        self.upd_cnt = 0
        self.lsn = 0
        self.seq = 0
        self.link = 0
        self.attr_off = 0
        self.flags = 0
        self.size = 0
        self.alloc_sizef = 0
        self.base_ref = 0
        self.next_attrid = 0
        self.recordnum = 0
        self.filename = ''
        self.parent_ref = 0
        self.filesize = 0
        
        self.si_times = {
            'crtime': WindowsTime(0, 0),
            'mtime': WindowsTime(0, 0),
            'atime': WindowsTime(0, 0),
            'ctime': WindowsTime(0, 0)
        }
        self.fn_times = {
            'crtime': WindowsTime(0, 0),
            'mtime': WindowsTime(0, 0),
            'atime': WindowsTime(0, 0),
            'ctime': WindowsTime(0, 0)
        }
        self.attribute_types: Set[int] = set()
        self.attribute_list: List[Dict] = []
        self.object_id = ''
        self.birth_volume_id = ''
        self.birth_object_id = ''
        self.birth_domain_id = ''

        self.security_descriptor: Optional[Dict] = None
        self.volume_name: Optional[str] = None
        self.volume_info: Optional[Dict] = None
        self.data_attribute: Optional[Dict] = None
        self.index_root: Optional[Dict] = None
        self.index_allocation: Optional[Dict] = None
        self.bitmap: Optional[Dict] = None
        self.reparse_point: Optional[Dict] = None
        self.ea_information: Optional[Dict] = None
        self.ea: Optional[Dict] = None
        self.logged_utility_stream: Optional[Dict] = None
        self.md5: Optional[str] = None
        self.sha256: Optional[str] = None
        self.sha512: Optional[str] = None
        self.crc32: Optional[str] = None
        
        if compute_hashes:
            self.compute_hashes()
        self.parse_record()

    def log(self, message: str, level: int = 0) -> None:

        if hasattr(self.logger, 'error'):
            if level == 0:
                self.logger.error(message)
            elif level == 1:
                self.logger.warning(message)
            elif level == 2:
                self.logger.info(message)
            else:
                self.logger.debug(message)
        else:
            self.logger(message, level)

    def parse_record(self) -> None:
        try:
            self.magic = struct.unpack("<I", self.raw_record[MFT_RECORD_MAGIC_NUMBER_OFFSET:MFT_RECORD_MAGIC_NUMBER_OFFSET+MFT_RECORD_MAGIC_NUMBER_SIZE])[0]
            self.upd_off = struct.unpack("<H", self.raw_record[MFT_RECORD_UPDATE_SEQUENCE_OFFSET:MFT_RECORD_UPDATE_SEQUENCE_OFFSET+MFT_RECORD_UPDATE_SEQUENCE_SIZE])[0]
            self.upd_cnt = struct.unpack("<H", self.raw_record[MFT_RECORD_UPDATE_SEQUENCE_SIZE_OFFSET:MFT_RECORD_UPDATE_SEQUENCE_SIZE_OFFSET+MFT_RECORD_UPDATE_SEQUENCE_SIZE_SIZE])[0]
            self.lsn = struct.unpack("<Q", self.raw_record[MFT_RECORD_LOGFILE_SEQUENCE_NUMBER_OFFSET:MFT_RECORD_LOGFILE_SEQUENCE_NUMBER_OFFSET+MFT_RECORD_LOGFILE_SEQUENCE_NUMBER_SIZE])[0]
            self.seq = struct.unpack("<H", self.raw_record[MFT_RECORD_SEQUENCE_NUMBER_OFFSET:MFT_RECORD_SEQUENCE_NUMBER_OFFSET+MFT_RECORD_SEQUENCE_NUMBER_SIZE])[0]
            self.link = struct.unpack("<H", self.raw_record[MFT_RECORD_HARD_LINK_COUNT_OFFSET:MFT_RECORD_HARD_LINK_COUNT_OFFSET+MFT_RECORD_HARD_LINK_COUNT_SIZE])[0]
            self.attr_off = struct.unpack("<H", self.raw_record[MFT_RECORD_FIRST_ATTRIBUTE_OFFSET:MFT_RECORD_FIRST_ATTRIBUTE_OFFSET+MFT_RECORD_FIRST_ATTRIBUTE_SIZE])[0]
            self.flags = struct.unpack("<H", self.raw_record[MFT_RECORD_FLAGS_OFFSET:MFT_RECORD_FLAGS_OFFSET+MFT_RECORD_FLAGS_SIZE])[0]
            self.size = struct.unpack("<I", self.raw_record[MFT_RECORD_USED_SIZE_OFFSET:MFT_RECORD_USED_SIZE_OFFSET+MFT_RECORD_USED_SIZE_SIZE])[0]
            self.alloc_sizef = struct.unpack("<I", self.raw_record[MFT_RECORD_ALLOCATED_SIZE_OFFSET:MFT_RECORD_ALLOCATED_SIZE_OFFSET+MFT_RECORD_ALLOCATED_SIZE_SIZE])[0]
            self.base_ref = struct.unpack("<Q", self.raw_record[MFT_RECORD_FILE_REFERENCE_OFFSET:MFT_RECORD_FILE_REFERENCE_OFFSET+MFT_RECORD_FILE_REFERENCE_SIZE])[0]
            self.next_attrid = struct.unpack("<H", self.raw_record[MFT_RECORD_NEXT_ATTRIBUTE_ID_OFFSET:MFT_RECORD_NEXT_ATTRIBUTE_ID_OFFSET+MFT_RECORD_NEXT_ATTRIBUTE_ID_SIZE])[0]
            self.recordnum = struct.unpack("<I", self.raw_record[MFT_RECORD_RECORD_NUMBER_OFFSET:MFT_RECORD_RECORD_NUMBER_OFFSET+MFT_RECORD_RECORD_NUMBER_SIZE])[0]
            
            self.parse_attributes()

        except struct.error as e:
            self.log(f"Error parsing MFT record header for record {self.recordnum}: {e}", 0)
        except Exception as e:
            self.log(f"Unexpected error parsing MFT record {self.recordnum}: {e}", 0)

    def parse_attributes(self) -> None:
        offset = int(self.attr_off)
        
        while offset < len(self.raw_record) - 8:
            try:
                self.log(f"Parsing attribute at offset {offset}", 3)
                
                attr_type = int(struct.unpack("<L", self.raw_record[offset:offset+4])[0])
                attr_len = int(struct.unpack("<L", self.raw_record[offset+4:offset+8])[0])
                
                self.log(f"Attribute type: {attr_type}, length: {attr_len}", 3)

                if attr_type == 0xffffffff or attr_len == 0:
                    self.log("End of attributes reached", 3)
                    break
                
                try:
                    validate_attribute_length(
                        attr_len=attr_len,
                        offset=offset,
                        record_size=len(self.raw_record),
                        attr_type=attr_type
                    )
                except ValidationError as e:
                    self.log(f"Attribute validation failed at record {getattr(self, 'recordnum', 'unknown')}: {e}", 0)
                    offset += 8
                    continue
                
                self.attribute_types.add(attr_type)

                if attr_type == STANDARD_INFORMATION_ATTRIBUTE:
                    self.parse_si_attribute(offset)
                elif attr_type == FILE_NAME_ATTRIBUTE:
                    self.parse_fn_attribute(offset)
                elif attr_type == ATTRIBUTE_LIST_ATTRIBUTE:
                    self.parse_attribute_list(offset)
                elif attr_type == OBJECT_ID_ATTRIBUTE:
                    self.parse_object_id_attribute(offset)
                elif attr_type == SECURITY_DESCRIPTOR_ATTRIBUTE:
                    self.parse_security_descriptor(offset)
                elif attr_type == VOLUME_NAME_ATTRIBUTE:
                    self.parse_volume_name(offset)
                elif attr_type == VOLUME_INFORMATION_ATTRIBUTE:
                    self.parse_volume_information(offset)
                elif attr_type == DATA_ATTRIBUTE:
                    self.parse_data(offset)
                elif attr_type == INDEX_ROOT_ATTRIBUTE:
                    self.parse_index_root(offset)
                elif attr_type == INDEX_ALLOCATION_ATTRIBUTE:
                    self.parse_index_allocation(offset)
                elif attr_type == BITMAP_ATTRIBUTE:
                    self.parse_bitmap(offset)
                elif attr_type == REPARSE_POINT_ATTRIBUTE:
                    self.parse_reparse_point(offset)
                elif attr_type == EA_INFORMATION_ATTRIBUTE:
                    self.parse_ea_information(offset)
                elif attr_type == EA_ATTRIBUTE:
                    self.parse_ea(offset)
                elif attr_type == LOGGED_UTILITY_STREAM_ATTRIBUTE:
                    self.parse_logged_utility_stream(offset)

                offset += attr_len

            except Exception as e:
                self.log(f"Error processing record {self.recordnum}: {str(e)}", 0)
                self.log(f"attr_type: {attr_type} (type: {type(attr_type)})", 3)
                self.log(f"attr_len: {attr_len} (type: {type(attr_len)})", 3)
                self.log(f"offset: {offset}", 3)
                if self.debug_level >= 2:
                    traceback.print_exc()
                offset += 1

    def parse_si_attribute(self, offset: int) -> None:
        try:
            si_data = self.raw_record[offset+24:offset+72]
            if len(si_data) >= 32:
                timestamps = struct.unpack("<QQQQ", si_data[:32])
                self.si_times = {
                    'crtime': WindowsTime(timestamps[0] & 0xFFFFFFFF, timestamps[0] >> 32),
                    'mtime': WindowsTime(timestamps[1] & 0xFFFFFFFF, timestamps[1] >> 32),
                    'ctime': WindowsTime(timestamps[2] & 0xFFFFFFFF, timestamps[2] >> 32),
                    'atime': WindowsTime(timestamps[3] & 0xFFFFFFFF, timestamps[3] >> 32)
                }
        except struct.error as e:
            self.log(f"Error parsing SI attribute for record {self.recordnum}: {e}", 1)

    def parse_fn_attribute(self, offset: int) -> None:
        try:
            fn_data = self.raw_record[offset+24:]
            if len(fn_data) >= 64:
                self.parent_ref = struct.unpack("<Q", fn_data[:8])[0] & 0x0000FFFFFFFFFFFF
                timestamps = struct.unpack("<QQQQ", fn_data[8:40])
                self.fn_times = {
                    'crtime': WindowsTime(timestamps[0] & 0xFFFFFFFF, timestamps[0] >> 32),
                    'mtime': WindowsTime(timestamps[1] & 0xFFFFFFFF, timestamps[1] >> 32),
                    'ctime': WindowsTime(timestamps[2] & 0xFFFFFFFF, timestamps[2] >> 32),
                    'atime': WindowsTime(timestamps[3] & 0xFFFFFFFF, timestamps[3] >> 32)
                }
                self.filesize = struct.unpack("<Q", fn_data[48:56])[0]
                name_len = struct.unpack("B", fn_data[64:65])[0]
                if len(fn_data) >= 66 + name_len * 2:
                    self.filename = fn_data[66:66+name_len*2].decode('utf-16-le', errors='replace')
        except struct.error as e:
            self.log(f"Error parsing FN attribute for record {self.recordnum}: {e}", 1)

    def parse_object_id_attribute(self, offset: int) -> None:
        try:
            obj_id_data = self.raw_record[offset+24:offset+88]
            if len(obj_id_data) >= 64:
                self.object_id = str(uuid.UUID(bytes_le=bytes(obj_id_data[:16])))
                self.birth_volume_id = str(uuid.UUID(bytes_le=bytes(obj_id_data[16:32])))
                self.birth_object_id = str(uuid.UUID(bytes_le=bytes(obj_id_data[32:48])))
                self.birth_domain_id = str(uuid.UUID(bytes_le=bytes(obj_id_data[48:64])))
        except (struct.error, ValueError) as e:
            self.log(f"Error parsing Object ID attribute for record {self.recordnum}: {e}", 1)
    
    def get_parent_record_num(self) -> int:
        return self.parent_ref & 0x0000FFFFFFFFFFFF

    def parse_attribute_list(self, offset: int) -> None:
        try:
            attr_content_offset = offset + struct.unpack("<H", self.raw_record[offset+20:offset+22])[0]
            attr_content_end = offset + struct.unpack("<L", self.raw_record[offset+4:offset+8])[0]
            
            while attr_content_offset < attr_content_end:
                try:
                    attr_type = struct.unpack("<L", self.raw_record[attr_content_offset:attr_content_offset+4])[0]
                    attr_len = struct.unpack("<H", self.raw_record[attr_content_offset+4:attr_content_offset+6])[0]
                    name_len = struct.unpack("B", self.raw_record[attr_content_offset+6:attr_content_offset+7])[0]
                    name_offset = struct.unpack("B", self.raw_record[attr_content_offset+7:attr_content_offset+8])[0]
                    
                    if name_len > 0:
                        name = self.raw_record[attr_content_offset+name_offset:attr_content_offset+name_offset+name_len*2].decode('utf-16-le', errors='replace')
                    else:
                        name = ""
                    
                    vcn = struct.unpack("<Q", self.raw_record[attr_content_offset+8:attr_content_offset+16])[0]
                    ref = struct.unpack("<Q", self.raw_record[attr_content_offset+16:attr_content_offset+24])[0] & 0x0000FFFFFFFFFFFF
                    
                    self.attribute_list.append({
                        'type': attr_type,
                        'name': name,
                        'vcn': vcn,
                        'reference': ref
                    })
                    
                    attr_content_offset += attr_len
                    if attr_len == 0: 
                        break
                except struct.error:
                    break
        except struct.error as e:
            self.log(f"Error parsing Attribute List for record {self.recordnum}: {e}", 1)

    def parse_security_descriptor(self, offset: int) -> None:
        try:
            sd_data = self.raw_record[offset+24:]
            if len(sd_data) >= 20:
                revision = struct.unpack("B", sd_data[0:1])[0]
                control = struct.unpack("<H", sd_data[2:4])[0]
                owner_offset = struct.unpack("<L", sd_data[4:8])[0]
                group_offset = struct.unpack("<L", sd_data[8:12])[0]
                sacl_offset = struct.unpack("<L", sd_data[12:16])[0]
                dacl_offset = struct.unpack("<L", sd_data[16:20])[0]
                
                self.security_descriptor = {
                    'revision': revision,
                    'control': control,
                    'owner_offset': owner_offset,
                    'group_offset': group_offset,
                    'sacl_offset': sacl_offset,
                    'dacl_offset': dacl_offset
                }
        except struct.error as e:
            self.log(f"Error parsing Security Descriptor attribute for record {self.recordnum}: {e}", 1)

    def parse_volume_name(self, offset: int) -> None:
        try:
            vn_data = self.raw_record[offset+24:]
            if len(vn_data) >= 2:
                try:
                    name_length = struct.unpack("<H", vn_data[:2])[0]
                    if name_length * 2 + 2 <= len(vn_data):
                        self.volume_name = vn_data[2:2+name_length*2].decode('utf-16-le', errors='replace')
                        return
                except (struct.error, UnicodeDecodeError):
                    pass
            
            self.volume_name = vn_data.decode('utf-16-le', errors='replace').rstrip('\x00')
        except struct.error as e:
            self.log(f"Error parsing Volume Name attribute for record {self.recordnum}: {e}", 1)

    def parse_volume_information(self, offset: int) -> None:
        try:
            vi_data = self.raw_record[offset+24:offset+48]
            if len(vi_data) >= 12:
                self.volume_info = {
                    'major_version': struct.unpack("B", vi_data[8:9])[0],
                    'minor_version': struct.unpack("B", vi_data[9:10])[0],
                    'flags': struct.unpack("<H", vi_data[10:12])[0]
                }
        except struct.error as e:
            self.log(f"Error parsing Volume Information attribute for record {self.recordnum}: {e}", 1)

    def parse_data(self, offset: int) -> None:
        try:
            data_header = self.raw_record[offset:offset+24]
            non_resident_flag = struct.unpack("B", data_header[8:9])[0]
            name_length = struct.unpack("B", data_header[9:10])[0]
            name_offset = struct.unpack("<H", data_header[10:12])[0]
            
            if name_length > 0:
                name = self.raw_record[offset+name_offset:offset+name_offset+name_length*2].decode('utf-16-le', errors='replace')
            else:
                name = ""
            
            content_size = None
            start_vcn = None
            last_vcn = None
            
            if non_resident_flag == 0: 
                content_size = struct.unpack("<L", data_header[16:20])[0]
                content_offset = struct.unpack("<H", data_header[20:22])[0]
            else:  
                start_vcn = struct.unpack("<Q", data_header[16:24])[0]
                last_vcn = struct.unpack("<Q", self.raw_record[offset+24:offset+32])[0]
            
            self.data_attribute = {
                'name': name,
                'non_resident': bool(non_resident_flag),
                'content_size': content_size if non_resident_flag == 0 else None,
                'start_vcn': start_vcn if non_resident_flag != 0 else None,
                'last_vcn': last_vcn if non_resident_flag != 0 else None
            }
        except struct.error as e:
            self.log(f"Error parsing Data attribute for record {self.recordnum}: {e}", 1)

    def parse_index_root(self, offset: int) -> None:
        try:
            ir_data = self.raw_record[offset+24:]
            attr_type = struct.unpack("<L", ir_data[:4])[0]
            collation_rule = struct.unpack("<L", ir_data[4:8])[0]
            index_alloc_size = struct.unpack("<L", ir_data[8:12])[0]
            clusters_per_index = struct.unpack("B", ir_data[12:13])[0]
            
            self.index_root = {
                'attr_type': attr_type,
                'collation_rule': collation_rule,
                'index_alloc_size': index_alloc_size,
                'clusters_per_index': clusters_per_index
            }
        except struct.error as e:
            self.log(f"Error parsing Index Root attribute for record {self.recordnum}: {e}", 1)

    def parse_index_allocation(self, offset: int) -> None:
        try:
            ia_data = self.raw_record[offset+24:]
            data_runs_offset = struct.unpack("<H", ia_data[:2])[0]
            self.index_allocation = {
                'data_runs_offset': data_runs_offset
            }
        except struct.error as e:
            self.log(f"Error parsing Index Allocation attribute for record {self.recordnum}: {e}", 1)

    def parse_bitmap(self, offset: int) -> None:
        try:
            bitmap_data = self.raw_record[offset+24:]
            bitmap_size = struct.unpack("<L", bitmap_data[:4])[0]
            self.bitmap = {
                'size': bitmap_size,
                'data': bitmap_data[4:4+bitmap_size]
            }
        except struct.error as e:
            self.log(f"Error parsing Bitmap attribute for record {self.recordnum}: {e}", 1)

    def parse_reparse_point(self, offset: int) -> None:
        try:
            rp_data = self.raw_record[offset+24:]
            reparse_tag = struct.unpack("<L", rp_data[:4])[0]
            reparse_data_length = struct.unpack("<H", rp_data[4:6])[0]
            self.reparse_point = {
                'reparse_tag': reparse_tag,
                'data_length': reparse_data_length,
                'data': rp_data[8:8+reparse_data_length]
            }
        except struct.error as e:
            self.log(f"Error parsing Reparse Point attribute for record {self.recordnum}: {e}", 1)

    def parse_ea_information(self, offset: int) -> None:
        try:
            eai_data = self.raw_record[offset+24:]
            ea_size = struct.unpack("<L", eai_data[:4])[0]
            ea_count = struct.unpack("<L", eai_data[4:8])[0]
            self.ea_information = {
                'ea_size': ea_size,
                'ea_count': ea_count
            }
        except struct.error as e:
            self.log(f"Error parsing EA Information attribute for record {self.recordnum}: {e}", 1)

    def parse_ea(self, offset: int) -> None:
        try:
            ea_data = self.raw_record[offset+24:]
            next_entry_offset = struct.unpack("<L", ea_data[:4])[0]
            flags = struct.unpack("B", ea_data[4:5])[0]
            name_length = struct.unpack("B", ea_data[5:6])[0]
            value_length = struct.unpack("<H", ea_data[6:8])[0]
            name = ea_data[8:8+name_length].decode('ascii', errors='replace')
            value = ea_data[8+name_length:8+name_length+value_length]
            
            self.ea = {
                'next_entry_offset': next_entry_offset,
                'flags': flags,
                'name': name,
                'value': value
            }
        except struct.error as e:
            self.log(f"Error parsing EA attribute for record {self.recordnum}: {e}", 1)

    def parse_logged_utility_stream(self, offset: int) -> None:
        try:
            lus_data = self.raw_record[offset+24:]
            stream_size = struct.unpack("<Q", lus_data[:8])[0]
            self.logged_utility_stream = {
                'size': stream_size,
                'data': lus_data[8:8+stream_size]
            }
        except struct.error as e:
            self.log(f"Error parsing Logged Utility Stream attribute for record {self.recordnum}: {e}", 1)

    def to_csv(self) -> List[Union[str, int]]:
        row = [
            self.recordnum,
            "Valid" if self.magic == int.from_bytes(MFT_RECORD_MAGIC, BYTE_ORDER) else "Invalid",
            "In Use" if self.flags & FILE_RECORD_IN_USE else "Not in Use",
            self.get_file_type(),
            self.seq,
            self.get_parent_record_num(),
            self.base_ref >> 48,
            
            self.filename, "",  
            
            self.si_times['crtime'].dtstr,
            self.si_times['mtime'].dtstr,
            self.si_times['atime'].dtstr,
            self.si_times['ctime'].dtstr,
            
            self.fn_times['crtime'].dtstr,
            self.fn_times['mtime'].dtstr,
            self.fn_times['atime'].dtstr,
            self.fn_times['ctime'].dtstr,
            
            self.object_id,
            self.birth_volume_id,
            self.birth_object_id,
            self.birth_domain_id,
            
            str(STANDARD_INFORMATION_ATTRIBUTE in self.attribute_types),
            str(ATTRIBUTE_LIST_ATTRIBUTE in self.attribute_types),
            str(FILE_NAME_ATTRIBUTE in self.attribute_types),
            str(VOLUME_NAME_ATTRIBUTE in self.attribute_types),
            str(VOLUME_INFORMATION_ATTRIBUTE in self.attribute_types),
            str(DATA_ATTRIBUTE in self.attribute_types),
            str(INDEX_ROOT_ATTRIBUTE in self.attribute_types),
            str(INDEX_ALLOCATION_ATTRIBUTE in self.attribute_types),
            str(BITMAP_ATTRIBUTE in self.attribute_types),
            str(REPARSE_POINT_ATTRIBUTE in self.attribute_types),
            str(EA_INFORMATION_ATTRIBUTE in self.attribute_types),
            str(EA_ATTRIBUTE in self.attribute_types),
            str(LOGGED_UTILITY_STREAM_ATTRIBUTE in self.attribute_types),
            
            str(self.attribute_list),
            str(self.security_descriptor),
            self.volume_name or "",
            str(self.volume_info),
            str(self.data_attribute),
            str(self.index_root),
            str(self.index_allocation),
            str(self.bitmap),
            str(self.reparse_point),
            str(self.ea_information),
            str(self.ea),
            str(self.logged_utility_stream)
        ]
        
        if self.md5 is not None:
            row.extend([self.md5, self.sha256, self.sha512, self.crc32])
        else:
            row.extend([""] * 4)
            
        return row

    def compute_hashes(self) -> None:

        try:
            md5 = hashlib.md5()
            sha256 = hashlib.sha256()
            sha512 = hashlib.sha512()
            
            md5.update(self.raw_record)
            sha256.update(self.raw_record)
            sha512.update(self.raw_record)
            
            self.md5 = md5.hexdigest()
            self.sha256 = sha256.hexdigest()
            self.sha512 = sha512.hexdigest()
            self.crc32 = format(zlib.crc32(self.raw_record) & 0xFFFFFFFF, '08x')
        except Exception as e:
            self.log(f"Error computing hashes for record {self.recordnum}: {e}", 0)

    def set_hashes(self, md5: str, sha256: str, sha512: str, crc32: str) -> None:

        self.md5 = md5
        self.sha256 = sha256
        self.sha512 = sha512
        self.crc32 = crc32

    def get_file_type(self) -> str:
        if self.flags & FILE_RECORD_IS_DIRECTORY:
            return "Directory"
        elif self.flags & FILE_RECORD_IS_EXTENSION:
            return "Extension"
        elif self.flags & FILE_RECORD_HAS_SPECIAL_INDEX:
            return "Special Index"
        else:
            return "File"
    
    def parse_object_id(self, offset: int) -> None:
        return self.parse_object_id_attribute(offset)