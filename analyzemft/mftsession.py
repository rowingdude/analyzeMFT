#!/usr/bin/env python

# Version 2.1
#
# Author: Benjamin Cance (bjc@tdx.li)
# Copyright Benjamin Cance 2024
#
# 2-Aug-24 
# - Updated to current PEP
# - Updated the file opening mode for CSV files to work with Python 3 ('w' instead of 'wb' and adding newline='').
# - Using f-strings for better readability and performance.
# - Removed unnecessary 0 check in get_folder_path
# 

VERSION='2.1.0'

import sys
import csv
from . import mft
from .mftutils import WindowsTime
from optparse import OptionParser

SIAttributeSizeXP = 72
SIAttributeSizeNT = 48

class MftSession:
    'Class to describe an entire MFT processing session'

    def __init__(self):
        self.mft = {}
        self.folders = {}
        self.debug = False
        
    def mft_options(self):
        parser = OptionParser()
        parser.set_defaults(debug=False, UseLocalTimezone=False, UseGUI=False)
        
        parser.add_option("-v", "--version", action="store_true", dest="version",
                          help="Report version and exit")
        
        parser.add_option("-f", "--file", dest="filename",
                          help="Read MFT from FILE", metavar="FILE")
        
        parser.add_option("-o", "--output", dest="output",
                          help="Write results to FILE", metavar="FILE")
        
        parser.add_option("-a", "--anomaly",
                          action="store_true", dest="anomaly",
                          help="Turn on anomaly detection")
        
        parser.add_option("-b", "--bodyfile", dest="bodyfile",
                          help="Write MAC information to bodyfile", metavar="FILE")
        
        parser.add_option("--bodystd", action="store_true", dest="bodystd",
                          help="Use STD_INFO timestamps for body file rather than FN timestamps")
        
        parser.add_option("--bodyfull", action="store_true", dest="bodyfull",
                          help="Use full path name + filename rather than just filename")
        
        parser.add_option("-c", "--csvtimefile", dest="csvtimefile",
                          help="Write CSV format timeline file", metavar="FILE")
        
        parser.add_option("-l", "--localtz",
                          action="store_true", dest="localtz",
                          help="Report times using local timezone")
        parser.add_option("--no-csv-header",
                          action="store_true", dest="no_csv_header", default=False,
                         help="Suppresses the CSV header")
    
        parser.add_option("-d", "--debug",
                          action="store_true", dest="debug",
                          help="turn on debugging output")
        
        (self.options, args) = parser.parse_args()
        
    def open_files(self):
        if self.options.version:
            print(f"Version is: {VERSION}")
            sys.exit()

        if self.options.filename is None:
            print("-f <filename> required.")
            sys.exit()

        if self.options.output is None and self.options.bodyfile is None and self.options.csvtimefile is None:
            print("-o <filename> or -b <filename> or -c <filename> required.")
            sys.exit()

        try:
            self.file_mft = open(self.options.filename, 'rb')
        except IOError:
            print(f"Unable to open file: {self.options.filename}")
            sys.exit()

        if self.options.output is not None:
            try:
                self.file_csv = csv.writer(open(self.options.output, 'w', newline=''), dialect=csv.excel, quoting=1)
            except (IOError, TypeError):
                print(f"Unable to open file: {self.options.output}")
                sys.exit()

        if self.options.bodyfile is not None:
            try:
                self.file_body = open(self.options.bodyfile, 'w')
            except IOError:
                print(f"Unable to open file: {self.options.bodyfile}")
                sys.exit()

        if self.options.csvtimefile is not None:
            try:
                self.file_csv_time = open(self.options.csvtimefile, 'w')
            except (IOError, TypeError):
                print(f"Unable to open file: {self.options.csvtimefile}")
                sys.exit()
    def process_mft_file(self) -> None:
        self.num_records = 0
        self.mft: Dict[int, Dict[str, Any]] = {}

        if self.options.output is not None and not self.options.no_csv_header:
            self.file_csv.writerow(mft.mft_to_csv('', True))

        # 1024 is valid for current version of Windows but should really get this value from somewhere
        RECORD_SIZE = 1024

        while True:
            raw_record = self.file_mft.read(RECORD_SIZE)
            if not raw_record:
                break

            if len(raw_record) < RECORD_SIZE:
                print(f"Warning: Incomplete record read. Expected {RECORD_SIZE} bytes, got {len(raw_record)} bytes.")
                break

            record = mft.parse_record(raw_record, self.options)
            
            if self.options.debug:
                print(record)

            self.mft[self.num_records] = record
            self.num_records += 1

        print(f"Processed {self.num_records} MFT records.")
        self.gen_filepaths()

    def print_records(self):
        for i in self.mft:
            try:
                if self.options.output is not None:
                    self.file_csv.writerow(mft.mft_to_csv(self.mft[i], False))
                if self.options.csvtimefile is not None:
                    self.file_csv_time.write(mft.mft_to_l2t(self.mft[i]))
                if self.options.bodyfile is not None:
                    self.file_body.write(mft.mft_to_body(self.mft[i], self.options.bodyfull, self.options.bodystd))
            except Exception as e:
                print(f"Error processing record {i}: {str(e)}")
                continue

    def get_folder_path(self, seqnum):
        if self.debug:
            print(f"Building Folder For Record Number ({seqnum})")

        if seqnum not in self.mft:
            return 'Orphan'

        # If we've already figured out the path name, just return it
        if self.mft[seqnum].get('filename', ''):
            return self.mft[seqnum]['filename']

        try:
            fn_record = self.mft[seqnum].get(('fn', 0), {})
            if fn_record.get('par_ref') == 5:  # Seq number 5 is "/", root of the directory
                last_fn_record = self.mft[seqnum].get(('fn', self.mft[seqnum].get('fncnt', 1) - 1), {})
                self.mft[seqnum]['filename'] = f"/{last_fn_record.get('name', 'UnknownName')}"
                return self.mft[seqnum]['filename']
        except Exception as e:
            self.mft[seqnum]['filename'] = 'NoFNRecord'
            return self.mft[seqnum]['filename']

        # Self referential parent sequence number. The filename becomes a NoFNRecord note
        if fn_record.get('par_ref') == seqnum:
            if self.debug:
                print(f"Error, self-referential, while trying to determine path for seqnum {seqnum}")
            last_fn_record = self.mft[seqnum].get(('fn', self.mft[seqnum].get('fncnt', 1) - 1), {})
            self.mft[seqnum]['filename'] = f"ORPHAN/{last_fn_record.get('name', 'UnknownName')}"
            return self.mft[seqnum]['filename']

        # We're not at the top of the tree and we've not hit an error
        parentpath = self.get_folder_path(fn_record.get('par_ref', 0))
        last_fn_record = self.mft[seqnum].get(('fn', self.mft[seqnum].get('fncnt', 1) - 1), {})
        self.mft[seqnum]['filename'] = f"{parentpath}/{last_fn_record.get('name', 'UnknownName')}"

        return self.mft[seqnum]['filename']

    def gen_filepaths(self):
        for i in self.mft:
            try:
                # If we've not already calculated the full path ....
                if not self.mft[i].get('filename'):
                    if self.mft[i].get('fncnt', 0) > 0:
                        self.get_folder_path(i)
                        if self.debug:
                            print(f"Filename (with path): {self.mft[i].get('filename', 'UnknownPath')}")
                    else:
                        self.mft[i]['filename'] = 'NoFNRecord'
            except Exception as e:
                print(f"Error processing record {i}: {str(e)}")
                self.mft[i]['filename'] = 'ErrorInProcessing'