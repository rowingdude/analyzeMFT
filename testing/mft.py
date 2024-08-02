#!/usr/bin/env python3
# 
# Author: Benjamin Cance bjc@tdx.li
# Name: mft.py
#
# Copyright (c) 2024 Benjamin Cance. All rights reserved.
# This software is distributed under the MIT License
#
# Date: May 2024
#
# # # # # # # # # # # # # # # # # # # # # NOTICE # # # # # # # # # # # # # # # # # # # # # #
#                                                                                          # 
#                              THIS FILE IS BEING DEPRECATED                               # 
#           IT IS IN THE PROCESS OF BEING MODULARIZED INTO SMALLER FUNCTION SPECIFIC FILES #
#                                                                                          # 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #  #

#!/usr/bin/env python3
#
# Author: Benjamin Cance bjc@tdx.li
# Name: mft.py
#
# Copyright (c) 2024 Benjamin Cance. All rights reserved.
# This software is distributed under the MIT License
#
# Date: July 2024
#
# 31-July-2024
#
#       Converted the endless 'elseif' blocks to a dictionary, which I feel is more readable.

import binascii
import json
import struct
from optparse import OptionParser

from analyzemft import bitparse
from analyzemft import mftutils


class MFTRecord:
    ATTRIBUTE_HANDLERS = {
        0x10: 'process_standard_information',
        0x20: 'process_attribute_list',
        0x30: 'process_file_name',
        0x40: 'process_object_id',
        0x50: 'process_security_descriptor',
        0x60: 'process_volume_name',
        0x70: 'process_volume_info',
        0x80: 'process_data_attribute',
        0x90: 'process_index_root',
        0xA0: 'process_index_allocation',
        0xB0: 'process_bitmap',
        0xC0: 'process_reparse_point',
        0xD0: 'process_ea_info',
        0xE0: 'process_ea',
        0xF0: 'process_property_set',
        0x100: 'process_logged_utility_stream',
    }

    def __init__(self, raw_record, options):
        self.raw_record = raw_record
        self.options = options
        self.record = {
            'filename': '',
            'notes': '',
            'ads': 0,
            'datacnt': 0,
        }
        self.record['fncnt'] = 0
        self.parse_record()

    def parse_record(self):
        self.decode_mft_header()

        # Apply the NTFS fixup on a 1024 byte record.
        if self.record['seq_number'] == self.raw_record[510:512] and self.record['seq_number'] == self.raw_record[1022:1024]:
            self.raw_record = self.raw_record[:510] + self.record['seq_attr1'] + self.raw_record[512:1022] + self.record['seq_attr2']

        if self.options.debug:
            print(f'-->Record number: {self.record["recordnum"]}\n\tMagic: {self.record["magic"]} Attribute offset: {self.record["attr_off"]} Flags: {hex(self.record["flags"])} Size:{self.record["size"]}')

        if self.record['magic'] == 0x44414142:
            if self.options.debug:
                print("BAAD MFT Record")
            self.record['baad'] = True
            return

        if self.record['magic'] != 0x454c4946:
            if self.options.debug:
                print("Corrupt MFT Record")
            self.record['corrupt'] = True
            return

        self.read_attributes()

        if self.options.anomaly:
            self.anomaly_detect()

    def read_attributes(self):
        read_ptr = self.record['attr_off']
        while read_ptr < 1024:
            atr_record = bitparse.decode_atr_header(self.raw_record[read_ptr:])
            if atr_record['type'] == 0xffffffff:  # End of attributes
                break

            if atr_record['nlen'] > 0:
                record_bytes = self.raw_record[
                    read_ptr + atr_record['name_off']: read_ptr + atr_record['name_off'] + atr_record['nlen'] * 2]
                atr_record['name'] = record_bytes.decode('utf-16').encode('utf-8')
            else:
                atr_record['name'] = ''

            if self.options.debug:
                print(f"Attribute type: {hex(atr_record['type'])} Length: {atr_record['len']} Res: {hex(atr_record['res'])}")

            handler_method = self.ATTRIBUTE_HANDLERS.get(atr_record['type'])
            if handler_method:
                getattr(self, handler_method)(atr_record, read_ptr)
            else:
                if self.options.debug:
                    print("Found an unknown attribute")

            if atr_record['len'] > 0:
                read_ptr += atr_record['len']
            else:
                if self.options.debug:
                    print("ATRrecord->len < 0, exiting loop")
                break

    def process_standard_information(self, atr_record, read_ptr):
        if self.options.debug:
            print(f"Standard Information:\n++Type: {hex(int(atr_record['type']))} Length: {atr_record['len']} Resident: {atr_record['res']} Name Len:{atr_record['nlen']} Name Offset: {atr_record['name_off']}")
        si_record = bitparse.decode_si_attribute(self.raw_record[read_ptr + atr_record['soff']:], self.options.localtz)
        self.record['si'] = si_record
        if self.options.debug:
            print(f"++CRTime: {si_record['crtime'].dtstr}\n++MTime: {si_record['mtime'].dtstr}\n++ATime: {si_record['atime'].dtstr}\n++EntryTime: {si_record['ctime'].dtstr}")

    def process_attribute_list(self, atr_record, read_ptr):
        if self.options.debug:
            print("Attribute list")
        if atr_record['res'] == 0:
            al_record = bitparse.decode_attribute_list(self.raw_record[read_ptr + atr_record['soff']:], self.record)
            self.record['al'] = al_record
            if self.options.debug:
                print(f"Name: {al_record['name']}")
        else:
            if self.options.debug:
                print("Non-resident Attribute List?")
            self.record['al'] = None

    def process_file_name(self, atr_record, read_ptr):
        if self.options.debug:
            print("File name record")
        fn_record = bitparse.decode_fn_attribute(self.raw_record[read_ptr + atr_record['soff']:], self.options.localtz, self.record)
        self.record['fn', self.record['fncnt']] = fn_record
        if self.options.debug:
            print(f"Name: {fn_record['name']} ({self.record['fncnt']})")
        self.record['fncnt'] += 1
        if fn_record['crtime'] != 0:
            if self.options.debug:
                print(f"\tCRTime: {fn_record['crtime'].dtstr} MTime: {fn_record['mtime'].dtstr} ATime: {fn_record['atime'].dtstr} EntryTime: {fn_record['ctime'].dtstr}")

    def process_object_id(self, atr_record, read_ptr):
        object_id_record = bitparse.decode_object_id(self.raw_record[read_ptr + atr_record['soff']:])
        self.record['objid'] = object_id_record
        if self.options.debug:
            print("Object ID")

    def process_volume_name(self, atr_record, read_ptr):
        self.record['volname'] = True
        if self.options.debug:
            print("Volume name")

    def process_volume_info(self, atr_record, read_ptr):
        if self.options.debug:
            print("Volume info attribute")
        volume_info_record = bitparse.decode_volume_info(self.raw_record[read_ptr + atr_record['soff']:], self.options)
        self.record['volinfo'] = volume_info_record

    def process_data_attribute(self, atr_record, read_ptr):
        if self.options.debug:
            print("Data Attribute")
        data_record = bitparse.decode_data_attribute(self.raw_record[read_ptr + atr_record['soff']:])
        if data_record:
            if self.record['filename'] == '':
                self.record['filename'] = data_record['filename']
            self.record['datacnt'] += 1
        self.record['ads'] += 1

    def process_index_root(self, atr_record, read_ptr):
        self.record['indexroot'] = True
        if self.options.debug:
            print("Index root")

    def process_index_allocation(self, atr_record, read_ptr):
        self.record['indexallocation'] = True
        if self.options.debug:
            print("Index allocation")

    def process_bitmap(self, atr_record, read_ptr):
        self.record['bitmap'] = True
        if self.options.debug:
            print("Bitmap")

    def process_reparse_point(self, atr_record, read_ptr):
        self.record['reparsepoint'] = True
        if self.options.debug:
            print("Reparse point")

    def process_ea_info(self, atr_record, read_ptr):
        self.record['eainfo'] = True
        if self.options.debug:
            print("EA Information")

    def process_ea(self, atr_record, read_ptr):
        self.record['ea'] = True
        if self.options.debug:
            print("EA")

    def process_property_set(self, atr_record, read_ptr):
        self.record['propertyset'] = True
        if self.options.debug:
            print("Property set")

    def process_logged_utility_stream(self, atr_record, read_ptr):
        self.record['loggedutility'] = True
        if self.options.debug:
            print("Logged utility stream")

    def anomaly_detect(self):
        if self.options.debug:
            print(f"Detecting anomalies in record {self.record['recordnum']}")


def parse_options():
    parser = OptionParser(usage="usage: %prog [options] <mft-record>")
    parser.add_option("-d", "--debug"  , action="store_true", dest   ="debug"  , default=False, help="Print debug information")
    parser.add_option("-a", "--anomaly", action="store_true", dest   ="anomaly", default=False, help="Detect anomalies")
    parser.add_option("-l", "--localtz",                      dest="localtz"   , default=None , help="Local timezone for timestamps")
    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.error("Please provide a MFT record file")

    return options, args[0]


def main():
    options, filename = parse_options()
    with open(filename, 'rb') as file:
        raw_record = file.read()

    mft_record = MFTRecord(raw_record, options)

    if options.debug:
        print("Record parsed successfully")

if __name__ == "__main__":
    main()
