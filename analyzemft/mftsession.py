#!/usr/bin/env python3

# Author: Benjamin Cance bjc@tdx.li
# Name: mftsession.py
#
# Copyright (c) 2024 Benjamin Cance. All rights reserved.
# This software is distributed under the MIT License
#
# Date: May 2024
#
# Change log:
#
#           31-July-2024
#               a. Bumped the version to v3.1 given the rework here.
#               b. Type hints added wherever possible
#               c. Created three new script files to modularize the functionality.
#                    -- We're going to merge basic changes first, and then refactor this into smaller files.
#               d. Deprecated optparse in favor of argparse 
#               e. Reworked integer division and byte handling


import os
import sys
from optparse           import OptionParser
from mftOptions         import parse_options
from mftFilePathBuilder import MftFilePathBuilder
from mftfileoperations  import open_files, process_mft_file, do_output

VERSION = "v3.1.0"

class MftSession:
    
    @staticmethod
    def fmt_excel(date_str):
        return '="{}"'.format(date_str)

    @staticmethod
    def fmt_norm(date_str):
        return date_str

    def __init__(self):
        self.mft               = {}
        self.fullmft           = {}
        self.folders           = {}
        self.debug             = False
        self.mftsize           = 0
        self.file_path_builder = None
        self.options           = None
        self.file_mft          = None
        self.file_csv          = None
        self.file_body         = None
        self.file_csv_time     = None

    def mft_options(self):
    
        self.options = parse_options()
        self.path_sep = '\\' if self.options.winpath else '/'

        if self.options.excel:
            self.options.date_formatter = MftSession.fmt_excel
        else:
            self.options.date_formatter = MftSession.fmt_norm
        
        # Initialize the file path builder
        self.file_path_builder = MftFilePathBuilder(self.options)

    def open_files(self):
    
        open_files(self)

    def sizecheck(self):
    
        self.mftsize = int(os.path.getsize(self.options.filename)) / 1024

        if self.options.debug:
            print('There are %d records in the MFT' % self.mftsize)

        if not self.options.inmemory:
            return

        sizeinbytes = self.mftsize * 4500

        if self.options.debug:
            print('Need %d bytes of memory to save into memory' % sizeinbytes)

        try:
            arr = []
            for _ in range(0, sizeinbytes // 10):
                arr.append(1)
        except MemoryError:
            print('Error: Not enough memory to store MFT in memory. Try running again without -s option')
            sys.exit()

    def process_mft_file(self):
    
        process_mft_file(self)

    def get_folder_path(self, seqnum: int) -> str:
    
        if self.debug:
            print(f"Building Folder For Record Number ({seqnum})")

        if seqnum not in self.mft:
            return 'Orphan'

        if self.mft[seqnum]['filename'] != '':
            return self.mft[seqnum]['filename']

        try:
            if self.mft[seqnum]['par_ref'] == 5:
                self.mft[seqnum]['filename'] = self.path_sep + self.mft[seqnum]['name'].decode()
                return self.mft[seqnum]['filename']
        except:
            self.mft[seqnum]['filename'] = 'NoFNRecord'
            return self.mft[seqnum]['filename']

        if self.mft[seqnum]['par_ref'] == seqnum:
            if self.debug:
                print(f"Error, self-referential, while trying to determine path for seqnum {seqnum}")
            self.mft[seqnum]['filename'] = 'ORPHAN' + self.path_sep + self.mft[seqnum]['name'].decode()
            return self.mft[seqnum]['filename']

        parentpath = self.get_folder_path(self.mft[seqnum]['par_ref'])
        self.mft[seqnum]['filename'] = parentpath + self.path_sep + self.mft[seqnum]['name'].decode()

        return self.mft[seqnum]['filename']

    def gen_filepaths(self):

        self.file_path_builder.build_filepaths()
