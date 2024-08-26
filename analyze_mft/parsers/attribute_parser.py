import struct
from analyze_mft.utilities.windows_time import WindowsTime
from analyze_mft.constants.constants import *

class AttributeParser:
    def __init__(self, raw_data, options):
        self.raw_data = raw_data
        self.options = options

    def parse_attribute_header(self):
        if len(self.raw_data) < 16:
            return None

        header = {
            'type': struct.unpack("<I", self.raw_data[:4])[0],
            'len': struct.unpack("<I", self.raw_data[4:8])[0],
            'non_resident': struct.unpack("B", self.raw_data[8:9])[0],
            'name_len': struct.unpack("B", self.raw_data[9:10])[0],
            'name_offset': struct.unpack("<H", self.raw_data[10:12])[0],
            'flags': struct.unpack("<H", self.raw_data[12:14])[0],
            'id': struct.unpack("<H", self.raw_data[14:16])[0]
        }

        if header['non_resident'] == 0:
            header['content_size'] = struct.unpack("<I", self.raw_data[16:20])[0]
            header['content_offset'] = struct.unpack("<H", self.raw_data[20:22])[0]
        else:
            header['starting_vcn'] = struct.unpack("<Q", self.raw_data[16:24])[0]
            header['last_vcn'] = struct.unpack("<Q", self.raw_data[24:32])[0]
            header['data_runs_offset'] = struct.unpack("<H", self.raw_data[32:34])[0]
            header['compression_unit'] = struct.unpack("<H", self.raw_data[34:36])[0]
            header['allocated_size'] = struct.unpack("<Q", self.raw_data[40:48])[0]
            header['real_size'] = struct.unpack("<Q", self.raw_data[48:56])[0]
            header['initialized_size'] = struct.unpack("<Q", self.raw_data[56:64])[0]

        return header

    def parse_standard_information(self, offset):
        data = self.raw_data[offset:]
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

    def parse_file_name(self, offset):
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

    def parse_attribute_list(self, offset):
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

    def parse_object_id(self, offset):
        data = self.raw_data[offset:]
        if len(data) < 64:
            return None

        return {
            'object_id': data[:16],
            'birth_volume_id': data[16:32],
            'birth_object_id': data[32:48],
            'domain_id': data[48:64]
        }

    def parse_volume_info(self, offset):
        data = self.raw_data[offset:]
        if len(data) < 12:
            return None

        return {
            'reserved': struct.unpack("<Q", data[:8])[0],
            'major_version': struct.unpack("B", data[8:9])[0],
            'minor_version': struct.unpack("B", data[9:10])[0],
            'flags': struct.unpack("<H", data[10:12])[0]
        }

    def parse_data(self, offset, size):
        return self.raw_data[offset:offset + size]

    def parse_index_root(self, offset):
        data = self.raw_data[offset:]
        if len(data) < 16:
            return None

        return {
            'attribute_type': struct.unpack("<I", data[:4])[0],
            'collation_rule': struct.unpack("<I", data[4:8])[0],
            'index_alloc_size': struct.unpack("<I", data[8:12])[0],
            'clusters_per_index_record': struct.unpack("B", data[12:13])[0]
        }

    def parse_index_allocation(self, offset):
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
            entry = self.parse_index_entry(data[entries_offset:])
            if entry is None:
                break
            index_allocation['entries'].append(entry)
            entries_offset += entry['length']

        return index_allocation

    def parse_index_entry(self, data):
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

    def parse_bitmap(self, offset, size):
        return self.raw_data[offset:offset + size]

    def parse_reparse_point(self, offset):
        data = self.raw_data[offset:]
        if len(data) < 8:
            return None

        return {
            'reparse_tag': struct.unpack("<I", data[:4])[0],
            'reparse_data_length': struct.unpack("<H", data[4:6])[0],
            'reserved': struct.unpack("<H", data[6:8])[0],
            'reparse_data': data[8:]
        }

    def parse_ea_information(self, offset):
        data = self.raw_data[offset:]
        if len(data) < 8:
            return None

        return {
            'ea_pack_size': struct.unpack("<H", data[:2])[0],
            'need_ea_count': struct.unpack("<H", data[2:4])[0],
            'unpacked_ea_size': struct.unpack("<I", data[4:8])[0]
        }


    def parse_ea(self, offset):
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

    def parse_logged_utility_stream(self, offset, size):
        return self.raw_data[offset:offset + size]