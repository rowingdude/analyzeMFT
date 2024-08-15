from .common_imports import *
class CSVWriter:
    def __init__(self, options, file_handler):
        self.options = options
        self.file_handler = file_handler
        self.csv_writer = csv.writer(file_handler.file_csv, quoting=csv.QUOTE_ALL) if file_handler.file_csv else None

    def write_csv_header(self):
        header = ['Record Number', 'Good', 'Active', 'Record type',
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
                  'Property Set', 'Logged Utility Stream', 'Log/Notes', 'STF FN Shift', 'uSec Zero']
        self.csv_writer.writerow(header)

    def write_csv_record(self, record):
        csv_record = self._prepare_csv_record(record)
        self.csv_writer.writerow(csv_record)

    def write_bodyfile(self, record):
        bodyfile_record = self._prepare_bodyfile_record(record)
        self.file_handler.file_body.write(bodyfile_record + '\n')

    def write_l2t(self, record):
        l2t_record = self._prepare_l2t_record(record)
        self.file_handler.file_csv_time.write(l2t_record + '\n')

    def _prepare_csv_record(self, record):
        csv_record = [
            str(record['recordnum']),
            self._decode_mft_magic(record),
            self._decode_mft_isactive(record),
            self._decode_mft_recordtype(record),
            str(record['seq'])
        ]

        # Parent File Record Number and Sequence Number
        if record['fncnt'] > 0:
            csv_record.extend([str(record['fn', 0]['par_ref']), str(record['fn', 0]['par_seq'])])
        else:
            csv_record.extend(['NoParent', 'NoParent'])

        if record['fncnt'] > 0 and 'si' in record:
            csv_record.extend([
                record['filename'],
                record['si']['crtime'].dtstr,
                record['si']['mtime'].dtstr,
                record['si']['atime'].dtstr,
                record['si']['ctime'].dtstr,
                record['fn', 0]['crtime'].dtstr,
                record['fn', 0]['mtime'].dtstr,
                record['fn', 0]['atime'].dtstr,
                record['fn', 0]['ctime'].dtstr
            ])
        elif 'si' in record:
            csv_record.extend([
                'NoFNRecord',
                record['si']['crtime'].dtstr,
                record['si']['mtime'].dtstr,
                record['si']['atime'].dtstr,
                record['si']['ctime'].dtstr,
                'NoFNRecord', 'NoFNRecord', 'NoFNRecord', 'NoFNRecord'
            ])
        else:
            csv_record.extend([
                'NoFNRecord',
                'NoSIRecord', 'NoSIRecord', 'NoSIRecord', 'NoSIRecord',
                'NoFNRecord', 'NoFNRecord', 'NoFNRecord', 'NoFNRecord'
            ])

        # Object ID, Birth Volume ID, Birth Object ID, Birth Domain ID
        csv_record.extend([
            record.get('objid', ''),
            record.get('birth_volume_id', ''),
            record.get('birth_object_id', ''),
            record.get('birth_domain_id', '')
        ])

        # Additional filenames and timestamps (for Filename #2, #3, #4)
        for i in range(1, 4):
            if record['fncnt'] > i:
                csv_record.extend([
                    record['fn', i]['name'],
                    record['fn', i]['crtime'].dtstr,
                    record['fn', i]['mtime'].dtstr,
                    record['fn', i]['atime'].dtstr,
                    record['fn', i]['ctime'].dtstr
                ])
            else:
                csv_record.extend(['', '', '', '', ''])

        # Attribute flags
        csv_record.extend([
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
        ])

        # Notes
        csv_record.append(record.get('notes', ''))

        # STF FN Shift and uSec Zero
        csv_record.append('Y' if record.get('stf-fn-shift') else 'N')
        csv_record.append('Y' if record.get('usec-zero') else 'N')

        return csv_record

    def _prepare_bodyfile_record(self, record):
        # Implement the logic from the original mft_to_body function
        return f"Placeholder for bodyfile record: {record['recordnum']}"

    def _prepare_l2t_record(self, record):
        # Implement the logic from the original mft_to_l2t function
        return f"Placeholder for l2t record: {record['recordnum']}"

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
        if flags & 0x0002:
            record_type = 'Folder'
        else:
            record_type = 'File'
        if flags & 0x0004:
            record_type += ' + Unknown1'
        if flags & 0x0008:
            record_type += ' + Unknown2'
        return record_type