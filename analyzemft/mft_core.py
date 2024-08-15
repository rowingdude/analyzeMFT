import logging
import struct
from dataclasses import dataclass, field
from typing import Dict, Any, BinaryIO, List, Optional
from mft_reference import MFTReference, AttributeType

@dataclass
class MFTRecord:
    raw_data: bytes
    parsed_data: Dict[str, Any] = field(default_factory=dict)
    parent_record: Optional['MFTRecord'] = None
    full_path: str = ''


    def __post_init__(self):
        try:
            self._parse()
        except Exception as e:
            logging.error(f"Error parsing MFT record: {e}")

    def _parse(self):
        if len(self.raw_data) < 48:
            logging.warning("Record too short, skipping")
            return

        try:
            header_format = "<IHHQHHHHIIQHHI"
            header_size = struct.calcsize(header_format)
            header_fields = struct.unpack(header_format, self.raw_data[:header_size])
            
            field_names = [
                'magic', 'usa_ofs', 'usa_count', 'lsn', 'sequence_number',
                'link_count', 'attrs_offset', 'flags', 'bytes_in_use',
                'bytes_allocated', 'base_record', 'next_attr_instance',
                'reserved', 'recordnum'
            ]
            
            self.parsed_data.update(dict(zip(field_names, header_fields)))
            self.parsed_data['decoded_flags'] = MFTReference.decode_mft_record_flags(self.parsed_data['flags'])
            self._parse_attributes()
            self._reconstruct_path()

        except struct.error as e:
            logging.error(f"Failed to parse basic fields in MFT record: {e}")
            return

        self._parse_attributes()

    def _parse_attributes(self):
        offset = self.parsed_data['attrs_offset']
        attr_count = 0
        self.parsed_data['attributes'] = []
        
        while offset < len(self.raw_data) - 8 and attr_count < 1000:
            attr_header = self.raw_data[offset:offset+16]
            if len(attr_header) < 16:
                break
            
            attr_type, attr_len = struct.unpack("<II", attr_header[:8])
            if attr_type == 0xFFFFFFFF:
                break

            attr_name = MFTReference.get_attribute_name(attr_type)
            logging.info(f"Parsing attribute {attr_count}: type={attr_type} ({attr_name}), length={attr_len}, offset={offset}")

            attr_data = self._parse_attribute(attr_type, offset, attr_len)
            
            self.parsed_data['attributes'].append({
                'type': attr_type,
                'name': attr_name,
                'data': attr_data
            })

            offset += attr_len
            attr_count += 1

        for attr in self.parsed_data['attributes']:
            if attr['type'] == AttributeType.FILE_NAME:
                self._parse_filename_attr(attr['data'])
            elif attr['type'] == AttributeType.STANDARD_INFORMATION:
                self._parse_standard_info_attr(attr['data'])

    def _parse_attribute(self, attr_type: int, offset: int, length: int) -> Dict[str, Any]:
        parsers = {
            AttributeType.STANDARD_INFORMATION: self._parse_standard_info_attr,
            AttributeType.FILE_NAME: self._parse_filename_attr,
            AttributeType.DATA: self._parse_data_attr,
            AttributeType.REPARSE_POINT: self._parse_reparse_point_attr
        }
        parser = parsers.get(attr_type, self._parse_unknown_attr)
        return parser(offset, length)

    def _parse_standard_info_attr(self, offset: int, length: int) -> Dict[str, Any]:
        try:
            si_format = "<QQQQII"
            si_size = struct.calcsize(si_format)
            si_data = struct.unpack(si_format, self.raw_data[offset+24:offset+24+si_size])
            
            data = {
                'crtime': si_data[0],
                'mtime': si_data[1],
                'ctime': si_data[2],
                'atime': si_data[3],
                'flags': si_data[4],
            }
            data['decoded_flags'] = MFTReference.decode_standard_information_flags(data['flags'])
            return data
        except struct.error as e:
            logging.error(f"Error parsing $STANDARD_INFORMATION attribute: {e}")
            return {}

    def _parse_filename_attr(self, offset: int, length: int) -> Dict[str, Any]:
        try:

            filename = data.get('filename', '')
            self.parsed_data['filename'] = self._handle_unicode_filename(filename)
            self.parsed_data['parent_ref'] = data.get('parent_ref')
            self.parsed_data['parent_seq'] = data.get('parent_seq')
            self.parsed_data['file_name_namespace'] = FileNameNamespace(data.get('namespace', 0)).name

            
            for ts_type in ['crtime', 'mtime', 'atime', 'ctime']:
                self.parsed_data[f'fn_{ts_type}'] = data.get(ts_type)

        except (struct.error, UnicodeDecodeError) as e:
            logging.error(f"Error parsing filename attribute: {e}")
            return {}

    def _parse_data_attr(self, offset: int, length: int) -> Dict[str, Any]:
        try:
            non_resident_flag = self.raw_data[offset+8]
            if non_resident_flag == 0:
                content_size, content_offset = struct.unpack("<IH", self.raw_data[offset+16:offset+22])
                return {
                    'resident': True,
                    'size': content_size,
                    'content': self.raw_data[offset+content_offset:offset+content_offset+content_size].hex()
                }
            else:
                start_vcn, end_vcn = struct.unpack("<QQ", self.raw_data[offset+16:offset+32])
                return {
                    'resident': False,
                    'start_vcn': start_vcn,
                    'end_vcn': end_vcn,
                }
        except struct.error as e:
            logging.error(f"Error parsing $DATA attribute: {e}")
            return {}

    def _parse_reparse_point_attr(self, offset: int, length: int) -> Dict[str, Any]:
        try:
            reparse_tag = struct.unpack("<I", self.raw_data[offset+16:offset+20])[0]
            return {
                'reparse_tag': reparse_tag,
                'tag_description': MFTReference.get_reparse_point_tag(reparse_tag)
            }
        except struct.error as e:
            logging.error(f"Error parsing reparse point attribute: {e}")
            return {}

    def _parse_unknown_attr(self, offset: int, length: int) -> Dict[str, Any]:
        return {'raw_data': self.raw_data[offset:offset+length].hex()}

    
    def _parse_standard_info_attr(self, data: Dict[str, Any]):
        
        for ts_type in ['crtime', 'mtime', 'atime', 'ctime']:
            self.parsed_data[f'si_{ts_type}'] = data.get(ts_type)

    def _handle_unicode_filename(self, filename: str) -> str:
        try:
            return filename.encode('ascii').decode('ascii')
        except UnicodeEncodeError:
            return ''.join(char if ord(char) < 128 else f'<U+{ord(char):04X}>' for char in filename)

    def _reconstruct_path(self):
        if self.parent_record is None:
            self.full_path = self.parsed_data.get('filename', '')
        else:
            self.full_path = f"{self.parent_record.full_path}/{self.parsed_data.get('filename', '')}"

    @property
    def is_directory(self) -> bool:
        return bool(self.parsed_data.get('flags', 0) & 0x0002)

    @property
    def is_active(self) -> bool:
        return bool(self.parsed_data.get('flags', 0) & 0x0001)

    @property
    def record_type(self) -> str:
        return 'Folder' if self.parsed_data.get('flags', 0) & 0x0002 else 'File'

from config import Config  # Import the Config class

class MFTAnalyzer:
    def __init__(self, config: Config):
        self.config = config
        self.records: Dict[int, MFTRecord] = {}

    def process_file(self, file: BinaryIO):
        for record_num, raw_record in enumerate(iter(lambda: file.read(1024), b'')):
            try:
                record = MFTRecord(raw_record)
                self.records[record_num] = record
                if record_num % 1000 == 0:
                    logging.info(f"Processed {record_num} records")
                if self.config.max_records > 0 and record_num >= self.config.max_records - 1:
                    logging.info(f"Reached maximum number of records ({self.config.max_records})")
                    break
            except Exception as e:
                logging.error(f"Error processing MFT record {record_num}: {e}")

    def _link_parent_records(self):
        for record in self.records.values():
            parent_ref = record.parsed_data.get('parent_ref')
            if parent_ref is not None and parent_ref in self.records:
                record.parent_record = self.records[parent_ref]

    def reconstruct_file_paths(self):
        for record in self.records.values():
            record._reconstruct_path()

    def detect_anomalies(self) -> List[str]:
        anomalies = []
        for record in self.records.values():
            if record.parsed_data.get('flags', 0) & 0x0001 == 0:  # Check if record is not in use
                anomalies.append(f"Record {record.parsed_data.get('recordnum')} is marked as not in use")
        return anomalies

    def _reconstruct_all_paths(self):
        for record in self.records.values():
            record._reconstruct_path()

    def get_file_by_path(self, path: str) -> Optional[MFTRecord]:
        for record in self.records.values():
            if record.full_path == path:
                return record
        return None