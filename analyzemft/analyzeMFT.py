#!/usr/bin/env python

# Author: David Kovar [dkovar <at> gmail [dot] com]
# Name: analyzeMFT.py
#
# Copyright (c) 2010 David Kovar. All rights reserved.
# This software is distributed under the Common Public License 1.0
#
# Date: May 2013
#



import struct
import sys
import ctypes
import re
import time
import unicodedata
import csv
import binascii
import os
import platform
from mftutils import mft_options, WindowsTime


# Globals

VERSION='2.0.2'

SIAttributeSizeXP = 72
SIAttributeSizeNT = 48


class MftSession:
     'Class to describe an entire MFT processing session'

     def __init__(self):
          self.mft = {}
          self.folders = {}
          self.debug = False

     def open_files(self):
          if (self.options.version == True):
               print("Version is: %s" % (VERSION))
               sys.exit()

          if self.options.filename == None:
               print "-f <filename> required."
               sys.exit()

          if self.options.output == None and self.options.bodyfile == None and self.options.csvtimefile == None:
               print "-o <filename> or -b <filename> or -c <filename> required."
               sys.exit()

          try:
               self.file_mft = open(self.options.filename, 'rb')
          except:
               print "Unable to open file: %s" % self.options.filename
               sys.exit()

          if self.options.output != None:
               try:
                    self.file_csv = csv.writer(open(self.options.output, 'wb'), dialect=csv.excel,quoting=1)
               except (IOError, TypeError):
                    print "Unable to open file: %s" % self.options.output
                    sys.exit()

          if self.options.bodyfile != None:
               try:
                    self.file_body = open(self.options.bodyfile, 'w')
               except:
                    print "Unable to open file: %s" % self.options.bodyfile
                    sys.exit()

          if self.options.csvtimefile != None:
               try:
                    self.file_csv_time = open(self.options.csvtimefile, 'w')
               except (IOError, TypeError):
                    print "Unable to open file: %s" % self.options.csvtimefile
                    sys.exit()

     def process_mft_file(self):

          # reset the file reading (since we did some pre-processing)
          # mft_file.seek(0)

          self.num_records = 0
          if self.options.output != None:
               self.file_csv.writerow(tmp_record.mft_to_csv(True))

          # 1024 is valid for current version of Windows but should really get this value from somewhere
          raw_record = self.file_mft.read(1024)

          while raw_record != "":

               record = parse_record(raw_record, self.options)
               if self.options.debug: print tmp_record.record
               self.mft[self.num_records] = record

               self.num_records = self.num_records + 1

    #           if self.num_records > 10000:
    #               break

               raw_record = self.file_mft.read(1024)

          self.gen_filepaths()

     def print_records(self):
          for i in self.mft:
               if self.options.output != None:
                    self.file_csv.writerow(self.mft[i].mft_to_csv(False))
               if self.options.csvtimefile != None:
                    self.file_csv_time.write(self.mft[i].mft_to_l2t())
               if self.options.bodyfile != None:
                    self.file_body.write(self.mft[i].mft_to_body(self.options.bodyfull, self.options.bodystd))

     def get_folder_path(self, seqnum):
          if self.debug: print "Building Folder For Record Number (%d)" % seqnum

          if seqnum not in self.mft:
               return 'Orphan'

          # If we've already figured out the path name, just return it
          if (self.mft[seqnum].record['filename']) != '':
               return self.mft[seqnum].record['filename']

          try:
#                if (self.mft[seqnum].record['fn',0]['par_ref'] == 0) or (self.mft[seqnum].record['fn',0]['par_ref'] == 5):  # There should be no seq number 0, not sure why I had that check in place.
               if (self.mft[seqnum].record['fn',0]['par_ref'] == 5): # Seq number 5 is "/", root of the directory
                    self.mft[seqnum].record['filename'] = '/' + self.mft[seqnum].record['fn',self.mft[seqnum].record['fncnt']-1]['name']
                    return self.mft[seqnum].record['filename']
          except:  # If there was an error getting the parent's sequence number, then there is no FN record
               self.mft[seqnum].record['filename'] = 'NoFNRecord'
               return self.mft[seqnum].record['filename']

          # Self referential parent sequence number. The filename becomes a NoFNRecord note
          if (self.mft[seqnum].record['fn',0]['par_ref']) == seqnum:
               if self.debug: print "Error, self-referential, while trying to determine path for seqnum %s" % seqnum
               self.mft[seqnum].record['filename'] = 'ORPHAN/' + self.mft[seqnum].record['fn',self.mft[seqnum].record['fncnt']-1]['name']
               return self.mft[seqnum].record['filename']

          # We're not at the top of the tree and we've not hit an error
          parentpath = self.get_folder_path((self.mft[seqnum].record['fn',0]['par_ref']))
          self.mft[seqnum].record['filename'] =  parentpath + '/' + self.mft[seqnum].record['fn',self.mft[seqnum].record['fncnt']-1]['name']

          return self.mft[seqnum].record['filename']


     def gen_filepaths(self):

          for i in self.mft:

  #            if filename starts with / or ORPHAN, we're done.
  #            else get filename of parent, add it to ours, and we're done.

               # If we've not already calculated the full path ....
               if (self.mft[i].record['filename']) == '':

                    if ( self.mft[i].record['fncnt'] > 0 ):
                         self.get_folder_path(i)
                         # self.mft[i].record['filename'] = self.mft[i].record['filename'] + '/' + self.mft[i].record['fn',self.mft[i].record['fncnt']-1]['name']
                         # self.mft[i].record['filename'] = self.mft[i].record['filename'].replace('//','/')
                         if self.debug: print "Filename (with path): %s" % self.mft[i].record['filename']
                    else:
                         self.mft[i].record['filename'] == 'NoFNRecord'




if __name__=="__main__":

     session = MftSession()
     session.options = mft_options()
     session.open_files()
     session.process_mft_file()
     session.print_records()
