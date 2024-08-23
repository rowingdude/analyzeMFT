from .mft_record import MFTRecord
from .logger import Logger
from .json_writer import JSONWriter
from .thread_manager   import ThreadManager
import concurrent.futures


class MFTParser:
    def __init__(self, options, file_handler, csv_writer):
        self.options = options
        self.file_handler = file_handler
        self.csv_writer = csv_writer
        self.mft = {}
        self.folders = {}
        self.logger = Logger(options)
        self.thread_manager = ThreadManager(options.thread_count)
        self.json_writer = JSONWriter(options, file_handler)
        self.num_records = 0

    def parse_mft_file(self):

        self.logger.info("Starting to parse MFT file...")

        if self.options.output is not None:
            self.csv_writer.write_csv_header()

        raw_records = self._read_all_records()
        self.logger.info(f"Read {len(raw_records)} raw records from MFT file.")

        if self.options.thread_count > 1:
            self.logger.verbose(f"Using {self.options.thread_count} threads for parsing.")
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.options.thread_count) as executor:
                futures = [executor.submit(self._parse_single_record, raw_record) for raw_record in raw_records]
                for future in concurrent.futures.as_completed(futures):
                    record = future.result()
                    if record:
                        self.mft[self.num_records] = record
                        self.num_records += 1
                        if self.num_records % 1000 == 0:
                            self.logger.verbose(f"Parsed {self.num_records} records...")
        else:
            for raw_record in raw_records:
                record = self._parse_single_record(raw_record)
                if record:
                    self.mft[self.num_records] = record
                    self.num_records += 1
                    if self.num_records % 1000 == 0:
                        self.logger.verbose(f"Parsed {self.num_records} records...")

        self.logger.info(f"Finished parsing MFT file. Total records: {self.num_records}")



    def _read_all_records(self):
        raw_records = []
        raw_record = self.file_handler.read_mft_record()
        while raw_record:
            raw_records.append(raw_record)
            raw_record = self.file_handler.read_mft_record()
        return raw_records

    def _parse_single_record(self, raw_record):

        try:
            mft_record = MFTRecord(raw_record, self.options, self.logger)
            record = mft_record.parse()

            if record is not None:
                self._parse_object_id(record)
                self._check_usec_zero(record)
                self.logger.debug(f"Parsed record {record['recordnum']}: filename={record.get('filename', 'N/A')}")
                
            return record

        except Exception as e:

            self.logger.error(f"Error parsing record: {str(e)}")
            return None

    def _check_usec_zero(self, record):
        if 'si' in record:
            si_times = [record['si']['crtime'], record['si']['mtime'], record['si']['atime'], record['si']['ctime']]
            record['usec-zero'] = all(time.unixtime % 1 == 0 for time in si_times)
            self.logger.debug(f"Record {record['recordnum']} usec-zero: {record['usec-zero']}")

    def _parse_object_id(self, record):
        if 'objid' in record:
            # Parse object ID data
            # This is a placeholder. You'll need to implement the actual parsing logic
            record['birth_volume_id'] = ''
            record['birth_object_id'] = ''
            record['birth_domain_id'] = ''
    
    def generate_filepaths(self):
        self.logger.info("Generating file paths...")
        for i in self.mft:
            if self.mft[i]['filename'] == '':
                if self.mft[i]['fncnt'] > 0:
                    self.get_folder_path(i)
                else:
                    self.mft[i]['filename'] = 'NoFNRecord'
        self.logger.info("Finished generating file paths.")

    def get_folder_path(self, seqnum, visited=None):
        if visited is None:
            visited = set()
        
        if seqnum in visited:
            return 'Circular_Reference'
        
        visited.add(seqnum)
        
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

        parentpath = self.get_folder_path(self.mft[seqnum]['fn', 0]['par_ref'], visited)
        self.mft[seqnum]['filename'] = parentpath + '/' + self.mft[seqnum]['fn', self.mft[seqnum]['fncnt'] - 1]['name']

        return self.mft[seqnum]['filename']

    def print_records(self):
        self.logger.info("Writing records to output files...")
        for i in self.mft:
            if self.options.output is not None:
                self.csv_writer.write_csv_record(self.mft[i])
            if self.options.csvtimefile is not None:
                self.csv_writer.write_l2t(self.mft[i])
            if self.options.bodyfile is not None:
                self.csv_writer.write_bodyfile(self.mft[i])
            if self.options.jsonfile is not None:
                self.json_writer.write_json_record(self.mft[i])

        # This writes the entire file, in the loop, we write (stage) records.
        if self.options.jsonfile is not None:
            self.json_writer.write_json_file()
        
        self.logger.info("Finished writing records to output files.")

