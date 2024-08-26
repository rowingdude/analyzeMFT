import csv
from io import StringIO
from typing import Dict, Any, List
from analyze_mft.constants.constants import CSV_HEADER

class CSVWriter:
    def __init__(self, options: Any, file_handler: Any):
        self.options = options
        self.file_handler = file_handler

    async def write_csv_header(self):
        await self.file_handler.write_csv(','.join(CSV_HEADER) + '\n')

    async def write_csv_record(self, record: Dict[str, Any]):
        csv_record = await self._prepare_csv_record(record)
        output = StringIO()
        csv.writer(output, quoting=csv.QUOTE_ALL).writerow(csv_record)
        await self.file_handler.write_csv(output.getvalue())

    async def _prepare_csv_record(self, record: Dict[str, Any]) -> List[str]:
        csv_record = [
            str(record['recordnum']),
            await self._decode_mft_magic(record),
            await self._decode_mft_isactive(record),
            await self._decode_mft_recordtype(record),
            str(record['seq'])
        ]
        
        csv_record.extend(await self._get_parent_file_info(record))
        csv_record.extend(await self._get_si_fn_info(record))
        csv_record.extend(await self._get_object_info(record))
        csv_record.extend(await self._get_additional_filenames_info(record))
        csv_record.extend(await self._get_attribute_flags(record))
        csv_record.extend(await self._get_notes_and_flags(record))
        
        return csv_record

    async def _decode_mft_magic(self, record: Dict[str, Any]) -> str:
        if record['magic'] == 0x454c4946:
            return "Good"
        elif record['magic'] == 0x44414142:
            return 'Bad'
        elif record['magic'] == 0x00000000:
            return 'Zero'
        else:
            return 'Unknown'

    async def _decode_mft_isactive(self, record: Dict[str, Any]) -> str:
        return 'Active' if record['flags'] & 0x0001 else 'Inactive'

    async def _decode_mft_recordtype(self, record: Dict[str, Any]) -> str:
        flags = int(record['flags'])
        if flags & RECORD_IS_DIRECTORY:
            record_type = 'Folder'
        else:
            record_type = 'File'
        if flags & RECORD_IS_4:
            record_type += ' + Unknown1'
        if flags & RECORD_IS_4_OR_8:
            record_type += ' + Unknown2'
        return record_type

    async def _get_parent_file_info(self, record: Dict[str, Any]) -> List[str]:
        if record['fncnt'] > 0:
            return [str(record['fn', 0]['par_ref']), str(record['fn', 0]['par_seq'])]
        else:
            return ['NoParent', 'NoParent']

    async def _get_si_fn_info(self, record: Dict[str, Any]) -> List[str]:
        if record['fncnt'] > 0 and 'si' in record:
            return [
                record['filename'],
                record['si']['crtime'].dtstr,
                record['si']['mtime'].dtstr,
                record['si']['atime'].dtstr,
                record['si']['ctime'].dtstr,
                record['fn', 0]['crtime'].dtstr,
                record['fn', 0]['mtime'].dtstr,
                record['fn', 0]['atime'].dtstr,
                record['fn', 0]['ctime'].dtstr
            ]
        elif 'si' in record:
            return [
                'NoFNRecord',
                record['si']['crtime'].dtstr,
                record['si']['mtime'].dtstr,
                record['si']['atime'].dtstr,
                record['si']['ctime'].dtstr,
                'NoFNRecord', 'NoFNRecord', 'NoFNRecord', 'NoFNRecord'
            ]
        else:
            return [
                'NoFNRecord',
                'NoSIRecord', 'NoSIRecord', 'NoSIRecord', 'NoSIRecord',
                'NoFNRecord', 'NoFNRecord', 'NoFNRecord', 'NoFNRecord'
            ]

    async def _get_object_info(self, record: Dict[str, Any]) -> List[str]:
        return [
            record.get('objid', ''),
            record.get('birth_volume_id', ''),
            record.get('birth_object_id', ''),
            record.get('birth_domain_id', '')
        ]

    async def _get_additional_filenames_info(self, record: Dict[str, Any]) -> List[str]:
        filenames_info = []
        for i in range(1, 4):
            if record['fncnt'] > i:
                filenames_info.extend([
                    record['fn', i]['name'],
                    record['fn', i]['crtime'].dtstr,
                    record['fn', i]['mtime'].dtstr,
                    record['fn', i]['atime'].dtstr,
                    record['fn', i]['ctime'].dtstr
                ])
            else:
                filenames_info.extend(['', '', '', '', ''])
        return filenames_info

    async def _get_attribute_flags(self, record: Dict[str, Any]) -> List[str]:
        return [
            'True' if 'si' in record else 'False',
            'True' if 'al' in record else 'False',
            'True' if record['fncnt'] > 0 else 'False',
            'True' if 'objid' in record else 'False',
            'True' if 'volname' in record else 'False',
            'True' if 'volinfo' in record else 'False',
            'True' if 'data' in record else 'False',
            'True' if 'indexroot' in record else 'False',
            'True' if 'indexallocation' in record else 'False',
            'True' if 'bitmap' in record else 'False',
            'True' if 'reparse' in record else 'False',
            'True' if 'eainfo' in record else 'False',
            'True' if 'ea' in record else 'False',
            'True' if 'propertyset' in record else 'False',
            'True' if 'loggedutility' in record else 'False'
        ]

    async def _get_notes_and_flags(self, record: Dict[str, Any]) -> List[str]:
        return [
            record.get('notes', ''),
            'Y' if record.get('stf-fn-shift') else 'N',
            'Y' if record.get('usec-zero') else 'N'
        ]