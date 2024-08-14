#!/usr/bin/env python

# Version 2.1.1
#
# Author: Benjamin Cance (bjc@tdx.li)
# Copyright Benjamin Cance 2024

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from .mft_utils import decodeMFTmagic, decodeMFTisactive, decodeMFTrecordtype

class MFTFormatter:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def format(self, record: Dict[str, Any], format_type: str, **kwargs) -> Any:
        if format_type == 'csv':
            return self.to_csv(record, kwargs.get('ret_header', False))
        elif format_type == 'body':
            return self.to_body(record, kwargs.get('full', False), kwargs.get('std', False))
        elif format_type == 'l2t':
            return self.to_l2t(record)
        elif format_type == 'json':
            return self.to_json(record)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")

    def to_csv(self, record: Dict[str, Any], ret_header: bool) -> List[str]:
        if ret_header:
            return self._generate_header()

        if 'baad' in record:
            return [str(record['recordnum']), "BAAD MFT Record"]

        csv_string = self._generate_base_record(record)

        if 'corrupt' in record:
            return csv_string + [str(record['recordnum']), "Corrupt", "Corrupt", "Corrupt MFT Record"]

        csv_string.extend(self._generate_file_info(record))
        csv_string.extend(self._generate_object_id(record))
        csv_string.extend(self._generate_additional_filenames(record))
        csv_string.extend(self._generate_attribute_flags(record))
        csv_string.extend(self._generate_additional_info(record))

        return [str(item) for item in csv_string]

    def _generate_base_record(self, record: Dict[str, Any]) -> List[str]:
        return [
            str(record['recordnum']),
            decodeMFTmagic(record),
            decodeMFTisactive(record),
            decodeMFTrecordtype(record),
            str(record.get('seq', ''))
        ]


    def to_body(self, record: Dict[str, Any], full: bool, std: bool) -> str:
        if record['fncnt'] > 0:
            name = self._get_filename(record, full)
            time_info = self._get_time_info(record, std)
            file_size = int(record['fn', 0]['real_fsize'])
        else:
            name, time_info, file_size = self._handle_no_fn_record(record)

        return self._format_bodyfile(name, file_size, time_info)

    def to_l2t(self, record: Dict[str, Any]) -> str:
        if record['fncnt'] > 0 or 'si' in record:
            return self._generate_l2t_entries(record)
        else:
            return self._generate_corrupt_l2t_entry(record)

    def to_json(self, record: Dict[str, Any]) -> str:
        try:
            sanitized_record = self._sanitize_record(record)
            return json.dumps(sanitized_record, indent=2)
        except (TypeError, ValueError) as e:
            self.logger.error(f"Error converting record to JSON: {e}")
            return "{}"

    def _generate_header(self) -> List[str]:
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
            'Property Set', 'Logged Utility Stream', 'Unknown Attributes', 'Log/Notes', 'STF FN Shift', 'uSec Zero'
        ]

    def _generate_base_record(self, record: Dict[str, Any]) -> List[str]:
        return [
            record['recordnum'],
            self._decode_mft_magic(record),
            self._decode_mft_is_active(record),
            self._decode_mft_record_type(record),
            str(record['seq']),
            str(record['seq'])
        ]

    def _generate_file_info(self, record: Dict[str, Any]) -> List[str]:
        if record['fncnt'] > 0:
            parent_info = [str(record['fn', 0]['par_ref']), str(record['fn', 0]['par_seq'])]
        else:
            parent_info = ['NoParent', 'NoParent']

        file_info = parent_info + self._generate_filename_buffer(record)
        return [str(item) for item in file_info] 

    def _generate_filename_buffer(self, record: Dict[str, Any]) -> List[str]:
        if record['fncnt'] > 0 and 'si' in record:
            return [
                record['filename'], str(record['si']['crtime'].dtstr),
                record['si']['mtime'].dtstr, record['si']['atime'].dtstr, record['si']['ctime'].dtstr,
                record['fn', 0]['crtime'].dtstr, record['fn', 0]['mtime'].dtstr,
                record['fn', 0]['atime'].dtstr, record['fn', 0]['ctime'].dtstr
            ]
        elif 'si' in record:
            return [
                'NoFNRecord', str(record['si']['crtime'].dtstr),
                record['si']['mtime'].dtstr, record['si']['atime'].dtstr, record['si']['ctime'].dtstr,
                'NoFNRecord', 'NoFNRecord', 'NoFNRecord', 'NoFNRecord'
            ]
        else:
            return ['NoFNRecord', 'NoSIRecord', 'NoSIRecord', 'NoSIRecord', 'NoSIRecord',
                    'NoFNRecord', 'NoFNRecord', 'NoFNRecord', 'NoFNRecord']

    def _generate_object_id(self, record: Dict[str, Any]) -> List[str]:
        if 'objid' in record:
            return [
                record['objid']['objid'], record['objid']['orig_volid'],
                record['objid']['orig_objid'], record['objid']['orig_domid']
            ]
        return ['', '', '', '']

    def _generate_additional_filenames(self, record: Dict[str, Any]) -> List[str]:
        result = []
        for i in range(1, record['fncnt']):
            result.extend([
                record['fn', i]['name'], record['fn', i]['crtime'].dtstr,
                record['fn', i]['mtime'].dtstr, record['fn', i]['atime'].dtstr,
                record['fn', i]['ctime'].dtstr
            ])
        
        padding = [''] * (15 - (5 * (record['fncnt'] - 1)))
        return result + padding

    def _generate_attribute_flags(self, record: Dict[str, Any]) -> List[str]:
        attributes = [
            'si', 'al', 'objid', 'volname', 'volinfo', 'data', 'indexroot',
            'indexallocation', 'bitmap', 'reparse', 'eainfo', 'ea',
            'propertyset', 'loggedutility'
        ]
        flags = ['True' if attr in record else 'False' for attr in attributes]
                
        if 'unknown_attributes' in record:
            flags.append(f"Unknown: {','.join(hex(attr) for attr in record['unknown_attributes'])}")
        else:
            flags.append('False')  
        
        return flags

    def _generate_additional_info(self, record: Dict[str, Any]) -> List[str]:
        return [
            'True' if record.get('fncnt', 0) > 0 else 'False',
            record.get('notes', 'None'),
            'Y' if 'stf-fn-shift' in record else 'N',
            'Y' if 'usec-zero' in record else 'N'
        ]

    def _get_filename(self, record: Dict[str, Any], full: bool) -> str:
        return record['filename'] if full else record['fn', 0]['name']

    def _get_time_info(self, record: Dict[str, Any], std: bool) -> Dict[str, int]:
        source = 'si' if std else ('fn', 0)
        return {
            'atime': int(record[source]['atime'].unixtime),
            'mtime': int(record[source]['mtime'].unixtime),
            'ctime': int(record[source]['ctime'].unixtime),
            'crtime': int(record[source]['crtime' if source == ('fn', 0) else 'ctime'].unixtime)
        }

    def _handle_no_fn_record(self, record: Dict[str, Any]) -> tuple:
        if 'si' in record:
            name = 'No FN Record'
            time_info = {
                'atime': int(record['si']['atime'].unixtime),
                'mtime': int(record['si']['mtime'].unixtime),
                'ctime': int(record['si']['ctime'].unixtime),
                'crtime': int(record['si']['ctime'].unixtime)
            }
            file_size = 0
        else:
            name = 'Corrupt Record'
            time_info = {'atime': 0, 'mtime': 0, 'ctime': 0, 'crtime': 0}
            file_size = 0
        return name, time_info, file_size

    def _format_bodyfile(self, name: str, file_size: int, time_info: Dict[str, int]) -> str:
        return f"0|{name}|0|0|0|0|{file_size}|{time_info['atime']}|{time_info['mtime']}|{time_info['ctime']}|{time_info['crtime']}\n"

    def _generate_l2t_entries(self, record: Dict[str, Any]) -> str:
        source = 'fn' if record['fncnt'] > 0 else 'si'
        index = 0 if source == 'fn' else None
        time_fields = ['atime', 'mtime', 'ctime', 'crtime']
        
        csv_strings = []
        for field in time_fields:
            date, time = record[source, index][field].dtstr.split(' ') if index is not None else record[source][field].dtstr.split(' ')
            type_str, macb_str = self._get_time_type_and_macb(field, source)
            
            csv_string = self._format_l2t_entry(date, time, macb_str, type_str, record)
            csv_strings.append(csv_string)
        
        return ''.join(csv_strings)

    def _get_time_type_and_macb(self, field: str, source: str) -> tuple:
        prefix = '$FN' if source == 'fn' else '$SI'
        if field == 'atime':
            return f'{prefix} [.A..] time', '.A..'
        elif field == 'mtime':
            return f'{prefix} [M...] time', 'M...'
        elif field == 'ctime':
            return f'{prefix} [..C.] time', '..C.'
        elif field == 'crtime':
            return f'{prefix} [...B] time', '...B'

    def _format_l2t_entry(self, date: str, time: str, macb_str: str, type_str: str, record: Dict[str, Any]) -> str:
        return f"{date}|{time}|TZ|{macb_str}|FILE|NTFS $MFT|{type_str}|user|host|{record['filename']}|desc|version|{record['filename']}|{record['seq']}|{record['notes']}|format|extra\n"

    def _generate_corrupt_l2t_entry(self, record: Dict[str, Any]) -> str:
        return f"-|-|TZ|unknown time|FILE|NTFS $MFT|unknown time|user|host|Corrupt Record|desc|version|NoFNRecord|{record['seq']}|-|format|extra\n"

    def _sanitize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = {}
        for key, value in record.items():
            if isinstance(value, dict):
                sanitized[key] = self._sanitize_record(value)
            elif hasattr(value, 'dtstr'):
                sanitized[key] = value.dtstr
            else:
                sanitized[key] = value
        return sanitized
    
    def _decode_mft_magic(self, record: Dict[str, Any]) -> str:
        return decodeMFTmagic(record)
    
    def _decode_mft_is_active(self, record: Dict[str, Any]) -> str:
        return decodeMFTisactive(record)

    def _decode_mft_record_type(self, record: Dict[str, Any]) -> str:
        return decodeMFTrecordtype(record)

def mft_to_csv(record: Dict[str, Any], ret_header: bool) -> List[str]:
    formatter = MFTFormatter()
    return formatter.format(record, 'csv', ret_header=ret_header)

def mft_to_body(record: Dict[str, Any], full: bool, std: bool) -> str:
    formatter = MFTFormatter()
    return formatter.format(record, 'body', full=full, std=std)

def mft_to_l2t(record: Dict[str, Any]) -> str:
    formatter = MFTFormatter()
    return formatter.format(record, 'l2t')

def mft_to_json(record: Dict[str, Any]) -> str:
    formatter = MFTFormatter()
    return formatter.format(record, 'json')