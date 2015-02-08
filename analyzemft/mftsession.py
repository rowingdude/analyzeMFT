#!/usr/bin/env python

# Author: David Kovar [dkovar <at> gmail [dot] com]
# Name: mftsession.py
#
# Copyright (c) 2010 David Kovar. All rights reserved.
# This software is distributed under the Common Public License 1.0
#
# Date: May 2013
#

VERSION = "v2.0.15"

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
          self.fullmft = {}
          self.folders = {}
          self.debug = False
          self.mftsize = 0
          
     def mft_options(self):
     
         parser = OptionParser()
         parser.set_defaults(inmemory=False, debug=False,UseLocalTimezone=False,UseGUI=False)
         
         parser.add_option("-v", "--version", action="store_true", dest="version",
                           help="report version and exit")
         
         parser.add_option("-f", "--file", dest="filename",
                           help="read MFT from FILE", metavar="FILE")
         
         parser.add_option("-o", "--output", dest="output",
                           help="write results to FILE", metavar="FILE")
         
         parser.add_option("-a", "--anomaly",
                           action="store_true", dest="anomaly",
                           help="turn on anomaly detection")

         parser.add_option("-e", "--excel",
                           action="store_true", dest="excel",
                           help="print date/time in Excel friendly format")
         
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
                           
         parser.add_option("-s", "--saveinmemory",
                           action="store_true", dest="inmemory",
                           help="Save a copy of the decoded MFT in memory. Do not use for very large MFTs")
                           
         parser.add_option("-p", "--progress",
                           action="store_true", dest="progress",
                           help="Show systematic progress reports.")                          
         
         (self.options, args) = parser.parse_args()
         
     def open_files(self):
          if (self.options.version == True):
               print("Version is: %s" % (VERSION))
               sys.exit()

          if self.options.filename == None:
               print "-f <filename> required."
               sys.exit()

          #if self.options.output == None and self.options.bodyfile == None and self.options.csvtimefile == None:
          #     print "-o <filename> or -b <filename> or -c <filename> required."
          #     sys.exit()

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



     #Provides a very rudimentary check to see if it's possible to store the entire MFT in memory
     #Not foolproof by any means, but could stop you from wasting time on a doomed to failure run.
     def sizecheck(self):
          
          #The number of records in the MFT is the size of the MFT / 1024
          self.mftsize = long(os.path.getsize(self.options.filename)) / 1024
          
          if self.options.debug: print 'There are %d records in the MFT' % self.mftsize
          
          if self.options.inmemory == False:
                  return
          
          #The size of the full MFT is approximately the number of records * the avg record size
          #Avg record size was determined empirically using some test data
          sizeinbytes = self.mftsize * 4500
          
          if self.options.debug: print 'Need %d bytes of memory to save into memory' % sizeinbytes
          
          try:
                  arr = []
                  for i in range(0, sizeinbytes/10):
                          arr.append(1)
          
          except(MemoryError):
                  print 'Error: Not enough memory to store MFT in memory. Try running again without -s option'
                  sys.exit()

     
     def process_mft_file(self):
          
          self.sizecheck()
          		 
          self.build_filepaths()
          
          #reset the file reading
          self.num_records = 0
          self.file_mft.seek(0)
          raw_record = self.file_mft.read(1024)

          
          if self.options.output != None:
               self.file_csv.writerow(mft.mft_to_csv(None, True, self.options))                    

          while raw_record != "":

               record = {}
               record = mft.parse_record(raw_record, self.options)
               if self.options.debug: print record
               
               record['filename'] = self.mft[self.num_records]['filename']

               self.do_output(record)
               
               self.num_records = self.num_records + 1
               
               if record['ads'] > 0:
                    for i in range(0, record['ads']):
#                         print "ADS: %s" % (record['data_name', i])
                         record_ads = record.copy()
                         record_ads['filename'] = record['filename'] + ':' + record['data_name', i]
                         self.do_output(record_ads)

               raw_record = self.file_mft.read(1024)   

     def do_output(self, record):
          
          if self.options.inmemory:
               self.fullmft[self.num_records] = record

          if self.options.output != None:
               self.file_csv.writerow(mft.mft_to_csv(record, False, self.options))

          if self.options.csvtimefile != None:
               self.file_csv_time.write(mft.mft_to_l2t(record))

          if self.options.bodyfile != None:
               self.file_body.write(mft.mft_to_body(record, self.options.bodyfull, self.options.bodystd))	

          if self.options.progress:
               if self.num_records % (self.mftsize/5) == 0 and self.num_records > 0:
                    print 'Building MFT: {0:.0f}'.format(100.0*self.num_records/self.mftsize) + '%'
          
     
     def plaso_process_mft_file(self):
          
          # TODO - Add ADS support ....
          
          self.build_filepaths()
          
          #reset the file reading
          self.num_records = 0
          self.file_mft.seek(0)
          raw_record = self.file_mft.read(1024)                  

          while raw_record != "":

               record = {}
               record = mft.parse_record(raw_record, self.options)
               if self.options.debug: print record
               
               record['filename'] = self.mft[self.num_records]['filename']
               
               self.fullmft[self.num_records] = record

               self.num_records = self.num_records + 1
  
               raw_record = self.file_mft.read(1024)
               
     def build_filepaths(self):
          # reset the file reading
          self.file_mft.seek(0)

          self.num_records = 0

          # 1024 is valid for current version of Windows but should really get this value from somewhere
          raw_record = self.file_mft.read(1024)
          while raw_record != "":

               record = {}
               minirec = {}
               record = mft.parse_record(raw_record, self.options)
               if self.options.debug: print record
               
               minirec['filename'] = record['filename']
               minirec['fncnt'] = record['fncnt']
               if record['fncnt'] == 1:
                    minirec['par_ref'] = record['fn',0]['par_ref']
                    minirec['name'] = record['fn',0]['name']
               if record['fncnt'] > 1:
                    minirec['par_ref'] = record['fn',0]['par_ref']
                    for i in (0, record['fncnt']-1):
                         #print record['fn',i]
                         if (record['fn', i]['nspace'] == 0x1 or record['fn', i]['nspace'] == 0x3):
                              minirec['name'] = record['fn', i]['name']
                    if (minirec.get('name') == None):
                         minirec['name'] = record['fn', record['fncnt']-1]['name']		
               
               self.mft[self.num_records] = minirec

               if self.options.progress:
                    if self.num_records % (self.mftsize/5) == 0 and self.num_records > 0:
                            print 'Building Filepaths: {0:.0f}'.format(100.0*self.num_records/self.mftsize) + '%'

               self.num_records = self.num_records + 1

               raw_record = self.file_mft.read(1024)

          self.gen_filepaths()


     def get_folder_path(self, seqnum):
          if self.debug: print "Building Folder For Record Number (%d)" % seqnum

          if seqnum not in self.mft:
               return 'Orphan'

          # If we've already figured out the path name, just return it
          if (self.mft[seqnum]['filename']) != '':
               return self.mft[seqnum]['filename']

          try:
#                if (self.mft[seqnum]['fn',0]['par_ref'] == 0) or (self.mft[seqnum]['fn',0]['par_ref'] == 5):  # There should be no seq number 0, not sure why I had that check in place.
               if (self.mft[seqnum]['par_ref'] == 5): # Seq number 5 is "/", root of the directory
                    self.mft[seqnum]['filename'] = '/' + self.mft[seqnum]['name']
                    return self.mft[seqnum]['filename']
          except:  # If there was an error getting the parent's sequence number, then there is no FN record
               self.mft[seqnum]['filename'] = 'NoFNRecord'
               return self.mft[seqnum]['filename']

          # Self referential parent sequence number. The filename becomes a NoFNRecord note
          if (self.mft[seqnum]['par_ref']) == seqnum:
               if self.debug: print "Error, self-referential, while trying to determine path for seqnum %s" % seqnum
               self.mft[seqnum]['filename'] = 'ORPHAN/' + self.mft[seqnum]['name']
               return self.mft[seqnum]['filename']

          # We're not at the top of the tree and we've not hit an error
          parentpath = self.get_folder_path((self.mft[seqnum]['par_ref']))
          self.mft[seqnum]['filename'] =  parentpath + '/' + self.mft[seqnum]['name']

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



