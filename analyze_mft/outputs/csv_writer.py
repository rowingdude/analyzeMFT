import csv
from io import StringIO
from analyze_mft.constants.constants import CSV_HEADER

class CSVWriter:
    def __init__(self, options, file_handler):
        self.options = options
        self.file_handler = file_handler
        self.csv_writer = csv.writer(StringIO(), quoting=csv.QUOTE_ALL)

    async def write_csv_header(self):
        if not self.csv_writer:
            print("Error: Attempting to write CSV header without a valid CSV writer.")
            return
        self.csv_writer.writerow(CSV_HEADER)
        await self.file_handler.file_csv.flush()

    async def write_csv_record(self, record):
        print(f"Writing CSV record for record number {record['recordnum']}")
        csv_record = self._prepare_csv_record(record)
        await self._write_csv_row(csv_record)
        print(f"Finished writing CSV record for record number {record['recordnum']}")

    async def _write_csv_row(self, row):
        output = StringIO()
        csv.writer(output, quoting=csv.QUOTE_ALL).writerow(row)
        await self.file_handler.write_csv(output.getvalue())
        print("CSV row written to file")

    def _prepare_csv_record(self, record):
        csv_record = [
            str(record['recordnum']),
            self._decode_mft_magic(record),
            self._decode_mft_isactive(record),
            self._decode_mft_recordtype(record),
            str(record['seq'])
        ]
        
        csv_record.extend(self._get_parent_file_info(record))
        csv_record.extend(self._get_si_fn_info(record))
        csv_record.extend(self._get_object_info(record))
        csv_record.extend(self._get_additional_filenames_info(record))
        csv_record.extend(self._get_attribute_flags(record))
        csv_record.extend(self._get_notes_and_flags(record))
        
        return csv_record

    def _get_parent_file_info(self, record):
        if record['fncnt'] > 0:
            return [str(record['fn', 0]['par_ref']), str(record['fn', 0]['par_seq'])]
        else:
            return ['NoParent', 'NoParent']

    def _get_si_fn_info(self, record):
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

    def _get_object_info(self, record):
        return [
            record.get('objid', ''),
            record.get('birth_volume_id', ''),
            record.get('birth_object_id', ''),
            record.get('birth_domain_id', '')
        ]

    def _get_additional_filenames_info(self, record):
        filenames_info = []
        for i in range(1, 4):
            if record['fncnt'] > 0 and 'si' in record:
                filenames_info.extend([
                    record['filename'],
                    str(record['si']['crtime']),
                    str(record['si']['mtime']),
                    str(record['si']['atime']),
                    str(record['si']['ctime']),
                    str(record['fn', 0]['crtime']),
                    str(record['fn', 0]['mtime']),
                    str(record['fn', 0]['atime']),
                    str(record['fn', 0]['ctime'])
                ])
            else:
                filenames_info.extend(['', '', '', '', ''])
        return filenames_info

    def _get_attribute_flags(self, record):
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

    def _get_notes_and_flags(self, record):
        return [
            record.get('notes', ''),
            'Y' if record.get('stf-fn-shift') else 'N',
            'Y' if record.get('usec-zero') else 'N'
        ]

    def _decode_mft_magic(self, record):
        if record['magic'] == 0x454c4946:
            return "Good"
        elif record['magic'] == 0x44414142:
            return 'Bad'
        elif record['magic'] == 0x00000000:
            return 'Zero'
        else:
            return 'Unknown'

    def _decode_mft_isactive(self, record):
        return 'Active' if record['flags'] & 0x0001 else 'Inactive'

    def _decode_mft_recordtype(self, record):
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