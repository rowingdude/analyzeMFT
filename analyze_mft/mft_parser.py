from .common_imports import *
from .mft_record import MFTRecord

class MFTParser:
    def __init__(self, options, file_handler, csv_writer):
        self.options = options
        self.file_handler = file_handler
        self.csv_writer = csv_writer
        self.mft = {}
        self.folders = {}

    def parse_mft_file(self):
        self.num_records = 0
        if self.options.output is not None:
            self.csv_writer.write_csv_header()

        raw_record = self.file_handler.read_mft_record()

        while raw_record:
            mft_record = MFTRecord(raw_record, self.options)
            record = mft_record.parse()
            
            self._parse_object_id(record)
            self._check_usec_zero(record)
            self.mft[self.num_records] = record
            self.num_records += 1
            raw_record = self.file_handler.read_mft_record()
    
    def _parse_object_id(self, record):
        if 'objid' in record:
            # Parse object ID data
            # This is a placeholder. You'll need to implement the actual parsing logic
            record['birth_volume_id'] = ''
            record['birth_object_id'] = ''
            record['birth_domain_id'] = ''

    def _check_usec_zero(self, record):
        if 'si' in record:
            si_times = [record['si']['crtime'], record['si']['mtime'], record['si']['atime'], record['si']['ctime']]
            record['usec-zero'] = all(time.unixtime % 1 == 0 for time in si_times)


    def generate_filepaths(self):
        for i in self.mft:
            if self.mft[i]['filename'] == '':
                if self.mft[i]['fncnt'] > 0:
                    self.get_folder_path(i)
                else:
                    self.mft[i]['filename'] = 'NoFNRecord'

    def get_folder_path(self, seqnum):
        if seqnum not in self.mft:
            return 'Orphan'

        if self.mft[seqnum]['filename'] != '':
            return self.mft[seqnum]['filename']

        try:
            if self.mft[seqnum]['fn', 0]['par_ref'] == 5:
                self.mft[seqnum]['filename'] = '/' + self.mft[seqnum]['fn', self.mft[seqnum]['fncnt'] - 1]['name']
                return self.mft[seqnum]['filename']
        except:
            self.mft[seqnum]['filename'] = 'NoFNRecord'
            return self.mft[seqnum]['filename']

        if self.mft[seqnum]['fn', 0]['par_ref'] == seqnum:
            self.mft[seqnum]['filename'] = 'ORPHAN/' + self.mft[seqnum]['fn', self.mft[seqnum]['fncnt'] - 1]['name']
            return self.mft[seqnum]['filename']

        parentpath = self.get_folder_path(self.mft[seqnum]['fn', 0]['par_ref'])
        self.mft[seqnum]['filename'] = parentpath + '/' + self.mft[seqnum]['fn', self.mft[seqnum]['fncnt'] - 1]['name']

        return self.mft[seqnum]['filename']

    def print_records(self):
        for i in self.mft:
            if self.options.output is not None:
                self.csv_writer.write_csv_record(self.mft[i])
            if self.options.csvtimefile is not None:
                self.csv_writer.write_l2t(self.mft[i])
            if self.options.bodyfile is not None:
                self.csv_writer.write_bodyfile(self.mft[i])