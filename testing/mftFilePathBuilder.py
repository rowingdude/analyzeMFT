#!/usr/bin/env python3
# Author: Benjamin Cance bjc@tdx.li
# Name: bitparse.py
#
# Copyright (c) 2024 Benjamin Cance. All rights reserved.
# This software is distributed under the MIT License
#
# Date: July 2024
#
# Factored out of mftSession.py
#
# Changes from the original:
#
#  31-July-2024
#
#    

from typing import Dict
from analyzemft import mft

class MftFilePathBuilder:
    def __init__(self, options):
        self.options = options
        self.mft = {}
        self.path_sep = '\\' if self.options.winpath else '/'

    def build_filepaths(self) -> None:
        
        self.num_records = 0
        self.file_mft.seek(0)
        raw_record = self.file_mft.read(1024)

        while raw_record != b"":
            minirec = {}
            record = mft.parse_record(raw_record, self.options)
            if self.options.debug:
                print(record)

            minirec['filename'] = record['filename']
            minirec['fncnt'] = record['fncnt']
            if record['fncnt'] == 1:
                minirec['par_ref'] = record['fn', 0]['par_ref']
                minirec['name'] = record['fn', 0]['name']
            elif record['fncnt'] > 1:
                minirec['par_ref'] = record['fn', 0]['par_ref']
                for i in range(record['fncnt']):
                    if record['fn', i]['nspace'] in (0x1, 0x3):
                        minirec['name'] = record['fn', i]['name']
                if 'name' not in minirec:
                    minirec['name'] = record['fn', record['fncnt'] - 1]['name']

            self.mft[self.num_records] = minirec

            if self.options.progress:
                if self.num_records % (self.mftsize // 5) == 0 and self.num_records > 0:
                    print(f'Building Filepaths: {100.0 * self.num_records / self.mftsize:.0f}%')

            self.num_records += 1
            raw_record = self.file_mft.read(1024)

        self.gen_filepaths()

    def get_folder_path(self, seqnum: int) -> str:
        if self.options.debug:
            print(f"Building Folder For Record Number ({seqnum})")

        if seqnum not in self.mft:
            return 'Orphan'

        if self.mft[seqnum]['filename'] != '':
            return self.mft[seqnum]['filename']

        try:
            if self.mft[seqnum]['par_ref'] == 5:
                self.mft[seqnum]['filename'] = self.path_sep + self.mft[seqnum]['name'].decode()
                return self.mft[seqnum]['filename']
        except KeyError:
            self.mft[seqnum]['filename'] = 'NoFNRecord'
            return self.mft[seqnum]['filename']

        if self.mft[seqnum]['par_ref'] == seqnum:
            if self.options.debug:
                print(f"Error, self-referential, while trying to determine path for seqnum {seqnum}")
            self.mft[seqnum]['filename'] = 'ORPHAN' + self.path_sep + self.mft[seqnum]['name'].decode()
            return self.mft[seqnum]['filename']

        parentpath = self.get_folder_path(self.mft[seqnum]['par_ref'])
        self.mft[seqnum]['filename'] = parentpath + self.path_sep + self.mft[seqnum]['name'].decode()

        return self.mft[seqnum]['filename']

    def gen_filepaths(self) -> None:
        for i in self.mft:
            if self.mft[i]['filename'] == '':
                if self.mft[i]['fncnt'] > 0:
                    self.get_folder_path(i)
                    if self.options.debug:
                        print(f"Filename (with path): {self.mft[i]['filename']}")
                else:
                    self.mft[i]['filename'] = 'NoFNRecord'
