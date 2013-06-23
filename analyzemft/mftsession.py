#!/usr/bin/env python

# Author: David Kovar [dkovar <at> gmail [dot] com]
# Name: analyzeMFT.py
#
# Copyright (c) 2010 David Kovar. All rights reserved.
# This software is distributed under the Common Public License 1.0
#
# Date: May 2013
#

VERSION='2.0.2'

import sys
import ctypes
import re
import time
import unicodedata
import csv
import os
import platform
from optparse import OptionParser
import mft

from mftutils import WindowsTime

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
         parser.set_defaults(debug=False,UseLocalTimezone=False,UseGUI=False)
         
         parser.add_option("-v", "--version", action="store_true", dest="version",
                           help="report version and exit")
         
         parser.add_option("-f", "--file", dest="filename",
                           help="read MFT from FILE", metavar="FILE")
         
         parser.add_option("-o", "--output", dest="output",
                           help="write results to FILE", metavar="FILE")
         
         parser.add_option("-a", "--anomaly",
                           action="store_true", dest="anomaly",
                           help="turn on anomaly detection")
         
         parser.add_option("-b", "--bodyfile", dest="bodyfile",
                           help="write MAC information to bodyfile", metavar="FILE")
         
         parser.add_option("--bodystd", action="store_true", dest="bodystd",
                           help="Use STD_INFO timestamps for body file rather than FN timestamps")
         
         parser.add_option("--bodyfull", action="store_true", dest="bodyfull",
                           help="Use full path name + filename rather than just filename")
         
         parser.add_option("-c", "--csvtimefile", dest="csvtimefile",
                           help="write CSV format timeline file", metavar="FILE")
         
         parser.add_option("-l", "--localtz",
                           action="store_true", dest="localtz",
                           help="report times using local timezone")
     
         parser.add_option("-d", "--debug",
                           action="store_true", dest="debug",
                           help="turn on debugging output")
         
         (self.options, args) = parser.parse_args()
         
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
               self.file_csv.writerow(mft.mft_to_csv('',True))

          # 1024 is valid for current version of Windows but should really get this value from somewhere
          raw_record = self.file_mft.read(1024)

          while raw_record != "":

               record = {}
               record = mft.parse_record(raw_record, self.options)
               if self.options.debug: print record
               self.mft[self.num_records] = record

               self.num_records = self.num_records + 1

    #           if self.num_records > 10000:
    #               break

               raw_record = self.file_mft.read(1024)

          self.gen_filepaths()

     def print_records(self):
          for i in self.mft:
               if self.options.output != None:
                    self.file_csv.writerow(mft.mft_to_csv(self.mft[i], False))
               if self.options.csvtimefile != None:
                    self.file_csv_time.write(mft.mft_to_l2t(self.mft[i]))
               if self.options.bodyfile != None:
                    self.file_body.write(mft.mft_to_body(self.mft[i], self.options.bodyfull, self.options.bodystd))

     def get_folder_path(self, seqnum):
          if self.debug: print "Building Folder For Record Number (%d)" % seqnum

          if seqnum not in self.mft:
               return 'Orphan'

          # If we've already figured out the path name, just return it
          if (self.mft[seqnum]['filename']) != '':
               return self.mft[seqnum]['filename']

          try:
#                if (self.mft[seqnum]['fn',0]['par_ref'] == 0) or (self.mft[seqnum]['fn',0]['par_ref'] == 5):  # There should be no seq number 0, not sure why I had that check in place.
               if (self.mft[seqnum]['fn',0]['par_ref'] == 5): # Seq number 5 is "/", root of the directory
                    self.mft[seqnum]['filename'] = '/' + self.mft[seqnum]['fn',self.mft[seqnum]['fncnt']-1]['name']
                    return self.mft[seqnum]['filename']
          except:  # If there was an error getting the parent's sequence number, then there is no FN record
               self.mft[seqnum]['filename'] = 'NoFNRecord'
               return self.mft[seqnum]['filename']

          # Self referential parent sequence number. The filename becomes a NoFNRecord note
          if (self.mft[seqnum]['fn',0]['par_ref']) == seqnum:
               if self.debug: print "Error, self-referential, while trying to determine path for seqnum %s" % seqnum
               self.mft[seqnum]['filename'] = 'ORPHAN/' + self.mft[seqnum]['fn',self.mft[seqnum]['fncnt']-1]['name']
               return self.mft[seqnum]['filename']

          # We're not at the top of the tree and we've not hit an error
          parentpath = self.get_folder_path((self.mft[seqnum]['fn',0]['par_ref']))
          self.mft[seqnum]['filename'] =  parentpath + '/' + self.mft[seqnum]['fn',self.mft[seqnum]['fncnt']-1]['name']

          return self.mft[seqnum]['filename']


     def gen_filepaths(self):

          for i in self.mft:

  #            if filename starts with / or ORPHAN, we're done.
  #            else get filename of parent, add it to ours, and we're done.

               # If we've not already calculated the full path ....
               if (self.mft[i]['filename']) == '':

                    if ( self.mft[i]['fncnt'] > 0 ):
                         self.get_folder_path(i)
                         # self.mft[i]['filename'] = self.mft[i]['filename'] + '/' + self.mft[i]['fn',self.mft[i]['fncnt']-1]['name']
                         # self.mft[i]['filename'] = self.mft[i]['filename'].replace('//','/')
                         if self.debug: print "Filename (with path): %s" % self.mft[i]['filename']
                    else:
                         self.mft[i]['filename'] == 'NoFNRecord'


