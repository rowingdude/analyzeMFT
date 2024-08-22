from .common_imports import *
from .thread_manager import ThreadManager


class CSVWriter:
    def __init__(self, options, file_handler):

        if not file_handler:
        
            print("Error: File handler not provided to CSVWriter.")
            sys.exit(1)
        
        self.options = options
        self.file_handler = file_handler
        self.thread_manager = ThreadManager(options.thread_count)
        
        if file_handler.file_csv:
        
            self.csv_writer = csv.writer(file_handler.file_csv, quoting=csv.QUOTE_ALL)
        
        else:
        
            self.csv_writer = None

            if options.output:
                print("Warning: CSV output file specified but not opened in file handler.")

    def write_csv_header(self):
        
        if not self.csv_writer:
            print("Error: Attempting to write CSV header without a valid CSV writer.")
            sys.exit(1)
            
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

        if self.options.thread_count > 1:
            self.thread_manager.map(self.write_csv_record, records)

        else:
            for record in records:
                self.write_csv_record(record)

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
            if record['fncnt'] > 0 and 'si' in record:
                csv_record.extend([
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
        bodyfile_parts = []

        # MD5 (we don't have this information, so we'll use a placeholder)
        bodyfile_parts.append('0')

        # Full path
        if self.options.bodyfull:
            full_path = record.get('filename', '')
        else:
            full_path = os.path.basename(record.get('filename', ''))
        bodyfile_parts.append(full_path)

        # Inode number
        bodyfile_parts.append(str(record['recordnum']))

        # Mode (we don't have exact permissions, so we'll use a placeholder)
        bodyfile_parts.append('0')

        # UID (we don't have this information)
        bodyfile_parts.append('0')

        # GID (we don't have this information)
        bodyfile_parts.append('0')

        # Size
        size = '0'
        if 'fn' in record and record['fncnt'] > 0:
            size = str(record['fn', 0].get('real_fsize', '0'))
        bodyfile_parts.append(size)

        # Timestamps
        timestamp_source = 'si' if self.options.bodystd else 'fn'
        
        if timestamp_source in record:
            atime = int(record[timestamp_source]['atime'].unixtime)
            mtime = int(record[timestamp_source]['mtime'].unixtime)
            ctime = int(record[timestamp_source]['ctime'].unixtime)
            crtime = int(record[timestamp_source]['crtime'].unixtime)
        else:
            atime = mtime = ctime = crtime = 0

        bodyfile_parts.extend([str(atime), str(mtime), str(ctime), str(crtime)])

        # Filename (for AFF4 support)
        bodyfile_parts.append(os.path.basename(full_path))

        return '|'.join(bodyfile_parts)

    def _prepare_l2t_record(self, record):
        l2t_record = []

        # Date format: MM/DD/YYYY HH:MM:SS
        date_format = "%m/%d/%Y %H:%M:%S"

        # Add timestamps (if available)
        if 'si' in record:
            l2t_record.extend([
                str(record['si']['crtime']),
                str(record['si']['mtime']),
                str(record['si']['atime']),
                str(record['si']['ctime'])
            ])
        else:
            l2t_record.extend(['', '', '', ''])

        # Add timezone
        l2t_record.append(self.options.localtz and 'LOCAL' or 'UTC')

        # Add MACB (Modified, Accessed, Created, Birth)
        l2t_record.append('MACB')

        # Add source
        l2t_record.append('FILE')

        # Add source_type
        l2t_record.append('MFT')

        # Add type
        l2t_record.append(self._decode_mft_recordtype(record))

        # Add user
        l2t_record.append('')  # We don't have user information in MFT records

        # Add host
        l2t_record.append('')  # We don't have host information in MFT records

        # Add short description (filename)
        l2t_record.append(record.get('filename', ''))

        # Add description (full path)
        l2t_record.append(record.get('filename', ''))

        # Add version
        l2t_record.append('')  # We don't have version information in MFT records

        # Add filename
        l2t_record.append(record.get('filename', ''))

        # Add inode
        l2t_record.append(str(record['recordnum']))

        # Add notes
        l2t_record.append(record.get('notes', ''))

        # Add format
        l2t_record.append('MFT')

        # Add extra
        extra = f"Seq: {record['seq']}"
        if 'fncnt' in record:
            extra += f", FN_count: {record['fncnt']}"
        l2t_record.append(extra)

        return '|'.join(l2t_record)

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