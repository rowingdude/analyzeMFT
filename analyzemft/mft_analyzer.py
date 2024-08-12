#!/usr/bin/env python

# Version 2.1.1
# Author: Benjamin Cance (bjc@tdx.li)
# Copyright Benjamin Cance 2024


from typing import Dict, Any
from .mftutils import WindowsTime

class MFTAnalyzer:
    def __init__(self, options):
        self.options = options
        self.mft = {}
        self.folders = {}
        self.num_records = 0

    def process_mft_file(self, file_mft):
        self.num_records = 0
        raw_record = file_mft.read(1024)

        while raw_record:
            record = self.parse_record(raw_record)
            if self.options.debug:
                print(record)
            self.mft[self.num_records] = record
            self.num_records += 1
            raw_record = file_mft.read(1024)

        self.gen_filepaths()


    def parse_record(raw_record: bytes, options: Any) -> Dict[str, Any]:
        record: Dict[str, Any] = {'filename': '', 'notes': '', 'fncnt': 0}

        decodeMFTHeader(record, raw_record)

        record_number = record['recordnum']

        if options.debug:
            print(f"-->Record number: {record_number}\n\tMagic: {record['magic']} Attribute offset: {record['attr_off']} Flags: {hex(int(record['flags']))} Size:{record['size']}")

        if record['magic'] == 0x44414142:
            if options.debug:
                print("BAAD MFT Record")
            record['baad'] = True
            return record

        if record['magic'] != 0x454c4946:
            if options.debug:
                print("Corrupt MFT Record")
            record['corrupt'] = True
            return record

        read_ptr = record['attr_off']

        while read_ptr < 1024:
            ATRrecord = decodeATRHeader(raw_record[read_ptr:])
            if ATRrecord['type'] == 0xffffffff:  
                break

            if options.debug:
                print(f"Attribute type: {ATRrecord['type']:x} Length: {ATRrecord['len']} Res: {ATRrecord['res']:x}")

            handler = attribute_handlers.get(ATRrecord['type'], handle_unknown_attribute)
            handler(ATRrecord, raw_record[read_ptr:], record, options)

            if ATRrecord['len'] > 0:
                read_ptr += ATRrecord['len']
            else:
                if options.debug:
                    print("ATRrecord->len <= 0, exiting loop")
                break

            pass

        def gen_filepaths(self):
            for i in self.mft:
                if self.mft[i]['filename'] == '':
                    if self.mft[i]['fncnt'] > 0:
                        self.get_folder_path(i)
                        if self.options.debug:
                            print(f"Filename (with path): {self.mft[i]['filename']}")
                    else:
                        self.mft[i]['filename'] = 'NoFNRecord'

     def get_folder_path(self, seqnum):
          if self.debug: print  ("Building Folder For Record Number (%d)" % seqnum)

          if seqnum not in self.mft:
               return 'Orphan'

          if (self.mft[seqnum]['filename']) != '':
               return self.mft[seqnum]['filename']

          try:
               if (self.mft[seqnum]['fn',0]['par_ref'] == 5): # Seq number 5 is "/", root of the directory
                    self.mft[seqnum]['filename'] = '/' + self.mft[seqnum]['fn',self.mft[seqnum]['fncnt']-1]['name']
                    return self.mft[seqnum]['filename']
          except: 
               self.mft[seqnum]['filename'] = 'NoFNRecord'
               return self.mft[seqnum]['filename']

          if (self.mft[seqnum]['fn',0]['par_ref']) == seqnum:
               if self.debug: print  ("Error, self-referential, while trying to determine path for seqnum %s" % seqnum)
               self.mft[seqnum]['filename'] = 'ORPHAN/' + self.mft[seqnum]['fn',self.mft[seqnum]['fncnt']-1]['name']
               return self.mft[seqnum]['filename']

          parentpath = self.get_folder_path((self.mft[seqnum]['fn',0]['par_ref']))
          self.mft[seqnum]['filename'] =  parentpath + '/' + self.mft[seqnum]['fn',self.mft[seqnum]['fncnt']-1]['name']

          return self.mft[seqnum]['filename']