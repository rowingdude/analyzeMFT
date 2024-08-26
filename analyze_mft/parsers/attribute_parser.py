import logging
import struct
from typing import Optional, Dict, Any, List
from analyze_mft.utilities.windows_time import WindowsTime
from analyze_mft.constants.constants import *

class AttributeParser:
    def __init__(self, raw_data: bytes, options: Any):
        self.raw_data = raw_data
        self.options = options
        self.logger = logging.getLogger('analyzeMFT')


    async def parse_attribute_header(self) -> Optional[Dict[str, Any]]:
        try:
            if len(self.raw_data) < 16:
                return None

            header = {
                'type': int.from_bytes(self.raw_data[:4], byteorder='little'),
                'len': int.from_bytes(self.raw_data[4:8], byteorder='little'),
                'non_resident': self.raw_data[8],
                'name_len': self.raw_data[9],
                'name_offset': int.from_bytes(self.raw_data[10:12], byteorder='little'),
                'flags': int.from_bytes(self.raw_data[12:14], byteorder='little'),
                'id': int.from_bytes(self.raw_data[14:16], byteorder='little')
            }

            if header['non_resident'] == 0:
                if len(self.raw_data) >= 24:
                    header['content_size'] = int.from_bytes(self.raw_data[16:20], byteorder='little')
                    header['content_offset'] = int.from_bytes(self.raw_data[20:22], byteorder='little')
            else:
                if len(self.raw_data) >= 64:
                    header['starting_vcn'] = int.from_bytes(self.raw_data[16:24], byteorder='little')
                    header['last_vcn'] = int.from_bytes(self.raw_data[24:32], byteorder='little')
                    header['data_runs_offset'] = int.from_bytes(self.raw_data[32:34], byteorder='little')
                    header['compression_unit'] = int.from_bytes(self.raw_data[34:36], byteorder='little')
                    header['allocated_size'] = int.from_bytes(self.raw_data[40:48], byteorder='little')
                    header['real_size'] = int.from_bytes(self.raw_data[48:56], byteorder='little')
                    header['initialized_size'] = int.from_bytes(self.raw_data[56:64], byteorder='little')

        except struct.error as e:
            self.logger.error(f"Error parsing attribute header: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error in parse_attribute_header: {str(e)}")
            return None

    async def parse_attribute(self, attr_type: int, attr_data: bytes) -> Optional[Dict[str, Any]]:
        try:
            if attr_type == STANDARD_INFORMATION:
                return await self.parse_standard_information(attr_data)
            elif attr_type == FILE_NAME:
                return await self.parse_file_name(attr_data)
            elif attr_type == OBJECT_ID:
                return await self.parse_object_id(attr_data)
            elif attr_type == DATA:
                return {'present': True}
            elif attr_type == INDEX_ROOT:
                return await self.parse_index_root(attr_data)
            elif attr_type == INDEX_ALLOCATION:
                return await self.parse_index_allocation(attr_data)
            elif attr_type == BITMAP:
                return {'present': True}
            elif attr_type == LOGGED_UTILITY_STREAM:
                return {'present': True}
            else:
                return {'type': attr_type, 'data': attr_data}
        except Exception as e:
            self.logger.error(f"Error parsing attribute {attr_type}: {str(e)}")
            return None


    async def parse_standard_information(self, data: bytes) -> Optional[Dict[str, Any]]:
        if len(data) < 72:
            return None

        return {
            'crtime': WindowsTime(struct.unpack("<Q", data[:8])[0], self.options.localtz),
            'mtime': WindowsTime(struct.unpack("<Q", data[8:16])[0], self.options.localtz),
            'ctime': WindowsTime(struct.unpack("<Q", data[16:24])[0], self.options.localtz),
            'atime': WindowsTime(struct.unpack("<Q", data[24:32])[0], self.options.localtz),
            'dos_flags': struct.unpack("<I", data[32:36])[0],
            'max_versions': struct.unpack("<I", data[36:40])[0],
            'version': struct.unpack("<I", data[40:44])[0],
            'class_id': struct.unpack("<I", data[44:48])[0],
            'owner_id': struct.unpack("<I", data[48:52])[0],
            'security_id': struct.unpack("<I", data[52:56])[0],
            'quota_charged': struct.unpack("<Q", data[56:64])[0],
            'usn': struct.unpack("<Q", data[64:72])[0]
        }

    async def parse_file_name(self, offset: int) -> Optional[Dict[str, Any]]:
        data = self.raw_data[offset:]
        if len(data) < 66:
            return None

        fn = {
            'parent_ref': struct.unpack("<Q", data[:8])[0],
            'crtime': WindowsTime(struct.unpack("<Q", data[8:16])[0], self.options.localtz),
            'mtime': WindowsTime(struct.unpack("<Q", data[16:24])[0], self.options.localtz),
            'ctime': WindowsTime(struct.unpack("<Q", data[24:32])[0], self.options.localtz),
            'atime': WindowsTime(struct.unpack("<Q", data[32:40])[0], self.options.localtz),
            'alloc_size': struct.unpack("<Q", data[40:48])[0],
            'real_size': struct.unpack("<Q", data[48:56])[0],
            'flags': struct.unpack("<I", data[56:60])[0],
            'reparse': struct.unpack("<I", data[60:64])[0],
            'name_length': struct.unpack("B", data[64:65])[0],
            'namespace': struct.unpack("B", data[65:66])[0]
        }

        name_offset = 66
        fn['name'] = data[name_offset:name_offset + fn['name_length'] * 2].decode('utf-16-le')

        return fn

    async def parse_attribute_list(self, offset: int) -> List[Dict[str, Any]]:
        data = self.raw_data[offset:]
        attributes = []

        while len(data) >= 26:
            attr = {
                'type': struct.unpack("<I", data[:4])[0],
                'length': struct.unpack("<H", data[4:6])[0],
                'name_length': struct.unpack("B", data[6:7])[0],
                'name_offset': struct.unpack("B", data[7:8])[0],
                'starting_vcn': struct.unpack("<Q", data[8:16])[0],
                'file_reference': struct.unpack("<Q", data[16:24])[0],
                'attribute_id': struct.unpack("<H", data[24:26])[0]
            }

            if attr['name_length'] > 0:
                name_offset = attr['name_offset']
                attr['name'] = data[name_offset:name_offset + attr['name_length'] * 2].decode('utf-16-le')
            else:
                attr['name'] = ''

            attributes.append(attr)
            data = data[attr['length']:]

        return attributes

    async def parse_object_id(self, offset: int) -> Optional[Dict[str, bytes]]:
        data = self.raw_data[offset:]
        if len(data) < 64:
            return None

        return {
            'object_id': data[:16],
            'birth_volume_id': data[16:32],
            'birth_object_id': data[32:48],
            'domain_id': data[48:64]
        }

    async def parse_volume_info(self, offset: int) -> Optional[Dict[str, Any]]:
        data = self.raw_data[offset:]
        if len(data) < 12:
            return None

        return {
            'reserved': struct.unpack("<Q", data[:8])[0],
            'major_version': struct.unpack("B", data[8:9])[0],
            'minor_version': struct.unpack("B", data[9:10])[0],
            'flags': struct.unpack("<H", data[10:12])[0]
        }

    async def parse_data(self, offset: int, size: int) -> bytes:
        return self.raw_data[offset:offset + size]

    async def parse_index_root(self, offset: int) -> Optional[Dict[str, Any]]:
        data = self.raw_data[offset:]
        if len(data) < 16:
            return None

        return {
            'attribute_type': struct.unpack("<I", data[:4])[0],
            'collation_rule': struct.unpack("<I", data[4:8])[0],
            'index_alloc_size': struct.unpack("<I", data[8:12])[0],
            'clusters_per_index_record': struct.unpack("B", data[12:13])[0]
        }

    async def parse_index_allocation(self, offset: int) -> Optional[Dict[str, Any]]:
        data = self.raw_data[offset:]
        if len(data) < 24:
            return None

        index_allocation = {
            'magic': struct.unpack("<I", data[:4])[0],
            'update_sequence_offset': struct.unpack("<H", data[4:6])[0],
            'update_sequence_size': struct.unpack("<H", data[6:8])[0],
            'lsn': struct.unpack("<Q", data[8:16])[0],
            'vcn': struct.unpack("<Q", data[16:24])[0],
            'entries': []
        }

        # Parse index entries
        entries_offset = 24
        while entries_offset < len(data) - 16:
            entry = await self.parse_index_entry(data[entries_offset:])
            if entry is None:
                break
            index_allocation['entries'].append(entry)
            entries_offset += entry['length']

        return index_allocation

    async def parse_index_entry(self, data: bytes) -> Optional[Dict[str, Any]]:
        if len(data) < 16:
            return None

        entry = {
            'file_reference': struct.unpack("<Q", data[:8])[0],
            'length': struct.unpack("<H", data[8:10])[0],
            'attribute_length': struct.unpack("<H", data[10:12])[0],
            'flags': struct.unpack("<I", data[12:16])[0]
        }

        if entry['length'] == 0:
            return None

        if entry['flags'] & 0x01:  # Has child node
            entry['subnode_vcn'] = struct.unpack("<Q", data[entry['length']-8:entry['length']])[0]

        return entry

    async def parse_bitmap(self, offset: int, size: int) -> bytes:
        return self.raw_data[offset:offset + size]

    async def parse_reparse_point(self, offset: int) -> Optional[Dict[str, Any]]:
        data = self.raw_data[offset:]
        if len(data) < 8:
            return None

        return {
            'reparse_tag': struct.unpack("<I", data[:4])[0],
            'reparse_data_length': struct.unpack("<H", data[4:6])[0],
            'reserved': struct.unpack("<H", data[6:8])[0],
            'reparse_data': data[8:]
        }

    async def parse_ea_information(self, offset: int) -> Optional[Dict[str, Any]]:
        data = self.raw_data[offset:]
        if len(data) < 8:
            return None

        return {
            'ea_pack_size': struct.unpack("<H", data[:2])[0],
            'need_ea_count': struct.unpack("<H", data[2:4])[0],
            'unpacked_ea_size': struct.unpack("<I", data[4:8])[0]
        }

    async def parse_ea(self, offset: int) -> List[Dict[str, Any]]:
        data = self.raw_data[offset:]
        eas = []

        while len(data) >= 8:
            ea = {
                'next_entry_offset': struct.unpack("<I", data[:4])[0],
                'flags': struct.unpack("B", data[4:5])[0],
                'name_length': struct.unpack("B", data[5:6])[0],
                'value_length': struct.unpack("<H", data[6:8])[0]
            }

            name_offset = 8
            ea['name'] = data[name_offset:name_offset + ea['name_length']].decode('ascii')

            value_offset = name_offset + ea['name_length'] + 1  # +1 for null terminator
            ea['value'] = data[value_offset:value_offset + ea['value_length']]

            eas.append(ea)

            if ea['next_entry_offset'] == 0:
                break
            data = data[ea['next_entry_offset']:]

        return eas

    async def parse_logged_utility_stream(self, offset: int, size: int) -> bytes:
        return self.raw_data[offset:offset + size]