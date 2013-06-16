#!/usr/bin/env python

# Author: David Kovar [dkovar <at> gmail [dot] com]
# Name: analyzeMFT.py
#
# Copyright (c) 2010 David Kovar. All rights reserved.
# This software is distributed under the Common Public License 1.0
#
# Date: May 2013
#

unicodeHack = True                           # This one is for me

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

VERSION='2.0.1'

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
          tmp_record = MftRecord()
          if self.options.output != None:
              self.file_csv.writerow(tmp_record.mft_to_csv(True))
          
          # 1024 is valid for current version of Windows but should really get this value from somewhere         
          raw_record = self.file_mft.read(1024)
          
          while raw_record != "":
              
              tmp_record = MftRecord()
              tmp_record.debug = self.options.debug
              tmp_record.localtz = self.options.localtz
              tmp_record.parse_record(raw_record)
              if self.debug: print tmp_record.record
              self.mft[self.num_records] = tmp_record
  
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


    
class MftRecord:
     'Common base class for all MFT records'

     def __init__(self):
          self.record = {}
          self.record['filename'] = ''
          self.record['notes'] = ''
 
     def parse_record(self, raw_record):
         
          self.decodeMFTHeader(raw_record);
         
          record_number = self.record['recordnum']
              
          if self.debug:
              print '-->Record number: %d\n\tMagic: %s Attribute offset: %d Flags: %s Size:%d' % (record_number, self.record['magic'],
                  self.record['attr_off'], hex(int(self.record['flags'])), self.record['size'])        
          
          if self.record['magic'] == 0x44414142:
              if self.debug:
                  print "BAAD MFT Record"
              self.record['baad'] = True
              return
  
          if self.record['magic'] != 0x454c4946:
              if self.debug:
                  print "Corrupt MFT Record"
              self.record['corrupt'] = True
              return
          
          read_ptr = self.record['attr_off']
              
          while (read_ptr < 1024):
           
               ATRrecord = self.decodeATRHeader(raw_record[read_ptr:])
               if ATRrecord['type'] == 0xffffffff:             # End of attributes
                    break
             
               if self.debug:
                    print "Attribute type: %x Length: %d Res: %x" % (ATRrecord['type'], ATRrecord['len'], ATRrecord['res'])
         
               if ATRrecord['type'] == 0x10:                   # Standard Information
                    if self.debug:
                         print "Stardard Information:\n++Type: %s Length: %d Resident: %s Name Len:%d Name Offset: %d" % \
                              (hex(int(ATRrecord['type'])),ATRrecord['len'],ATRrecord['res'],ATRrecord['nlen'],ATRrecord['name_off'])
                    SIrecord = self.decodeSIAttribute(raw_record[read_ptr+ATRrecord['soff']:])
                    self.record['si'] = SIrecord
                    if self.debug:
                         print "++CRTime: %s\n++MTime: %s\n++ATime: %s\n++EntryTime: %s" % \
                            (SIrecord['crtime'].dtstr, SIrecord['mtime'].dtstr, SIrecord['atime'].dtstr, SIrecord['ctime'].dtstr)
                 
               elif ATRrecord['type'] == 0x20:                 # Attribute list
                    if self.debug:
                        print "Attribute list"
                    if ATRrecord['res'] == 0:
                         ALrecord = self.decodeAttributeList(raw_record[read_ptr+ATRrecord['soff']:])
                         self.record['al'] = ALrecord
                         if self.debug:
                             print "Name: %s"  % (ALrecord['name'])
                    else:
                         if self.debug:
                             print "Non-resident Attribute List?"
                         self.record['al'] = None
                          
               elif ATRrecord['type'] == 0x30:                 # File name
                         if self.debug: print "File name record"
                         FNrecord = self.decodeFNAttribute(raw_record[read_ptr+ATRrecord['soff']:])
                         self.record['fn',self.record['fncnt']] = FNrecord
                         if self.debug: print "Name: %s (%d)" % (FNrecord['name'],self.record['fncnt'])
                         self.record['fncnt'] = self.record['fncnt'] + 1
                         if FNrecord['crtime'] != 0:
                             if self.debug: print "\tCRTime: %s MTime: %s ATime: %s EntryTime: %s" % (FNrecord['crtime'].dtstr,
                                     FNrecord['mtime'].dtstr, FNrecord['atime'].dtstr, FNrecord['ctime'].dtstr)
              
               elif ATRrecord['type'] == 0x40:                 #  Object ID
                    ObjectIDRecord = self.decodeObjectID(raw_record[read_ptr+ATRrecord['soff']:])
                    self.record['objid'] = ObjectIDRecord
                    if self.debug: print "Object ID"
                    
               elif ATRrecord['type'] == 0x50:                 # Security descriptor
                    self.record['sd'] = True
                    if self.debug: print "Security descriptor"
        
               elif ATRrecord['type'] == 0x60:                 # Volume name
                    self.record['volname'] = True
                    if self.debug: print "Volume name"
                    
               elif ATRrecord['type'] == 0x70:                 # Volume information
                    if self.debug: print "Volume info attribute"
                    VolumeInfoRecord = self.decodeVolumeInfo(raw_record[read_ptr+ATRrecord['soff']:])
                    self.record['volinfo'] = VolumeInfoRecord
                    
               elif ATRrecord['type'] == 0x80:                 # Data
                    self.record['data'] = True
                    if self.debug: print "Data attribute"
        
               elif ATRrecord['type'] == 0x90:                 # Index root
                    self.record['indexroot'] = True
                    if self.debug: print "Index root"
        
               elif ATRrecord['type'] == 0xA0:                 # Index allocation
                    self.record['indexallocation'] = True
                    if self.debug: print "Index allocation"
                    
               elif ATRrecord['type'] == 0xB0:                 # Bitmap
                    self.record['bitmap'] = True
                    if self.debug: print "Bitmap"
        
               elif ATRrecord['type'] == 0xC0:                 # Reparse point
                    self.record['reparsepoint'] = True
                    if self.debug: print "Reparse point"
        
               elif ATRrecord['type'] == 0xD0:                 # EA Information
                    self.record['eainfo'] = True
                    if self.debug: print "EA Information"
         
               elif ATRrecord['type'] == 0xE0:                 # EA
                    self.record['ea'] = True
                    if self.debug: print "EA"
        
               elif ATRrecord['type'] == 0xF0:                 # Property set
                    self.record['propertyset'] = True
                    if self.debug: print "Property set"
        
               elif ATRrecord['type'] == 0x100:                 # Logged utility stream
                    self.record['loggedutility'] = True
                    if self.debug: print "Logged utility stream"
                    
               else:
                    if self.debug: print "Found an unknown attribute"
                    
               if ATRrecord['len'] > 0:
                    read_ptr = read_ptr + ATRrecord['len']
               else:
                    if self.debug: print "ATRrecord->len < 0, exiting loop"
                    break
                            
     
     def mft_to_csv(self, ret_header):
          'Return a MFT record in CSV format'
         
          mftBuffer = ''
          tmpBuffer = ''
          filenameBuffer = ''
         
          if ret_header == True:
               # Write headers
               csv_string = ['Record Number', 'Good', 'Active', 'Record type',
     #                        '$Logfile Seq. Num.',
                              'Sequence Number', 'Parent File Rec. #', 'Parent File Rec. Seq. #',
                              'Filename #1', 'Std Info Creation date', 'Std Info Modification date',
                              'Std Info Access date', 'Std Info Entry date', 'FN Info Creation date',
                              'FN Info Modification date','FN Info Access date', 'FN Info Entry date',
                              'Object ID', 'Birth Volume ID', 'Birth Object ID', 'Birth Domain ID',
                              'Filename #2', 'FN Info Creation date', 'FN Info Modify date',
                              'FN Info Access date', 'FN Info Entry date', 'Filename #3', 'FN Info Creation date',
                              'FN Info Modify date', 'FN Info Access date',	'FN Info Entry date', 'Filename #4',
                              'FN Info Creation date', 'FN Info Modify date', 'FN Info Access date',
                              'FN Info Entry date', 'Standard Information', 'Attribute List', 'Filename',
                              'Object ID', 'Volume Name', 'Volume Info', 'Data', 'Index Root',
                              'Index Allocation', 'Bitmap', 'Reparse Point', 'EA Information', 'EA',
                              'Property Set', 'Logged Utility Stream', 'Log/Notes', 'STF FN Shift', 'uSec Zero']
               return csv_string
  
          if 'baad' in self.record:
               csv_string = ["%s" % self.record['recordnum'],"BAAD MFT Record"]
               return csv_string
  
          csv_string = [self.record['recordnum'], self.decodeMFTmagic(), self.decodeMFTisactive(),
                          self.decodeMFTrecordtype()]
          
          if 'corrupt' in self.record:
              tmp_string = ["%s" % self.record['recordnum'],"Corrupt","Corrupt","Corrupt MFT Record"]
              csv_string.extend(tmp_string)
              return csv_string
  
  #        tmp_string = ["%d" % self.record['lsn']]
  #        csv_string.extend(tmp_string)
          tmp_string = ["%d" % self.record['seq']]
          csv_string.extend(tmp_string)
        
          if self.record['fncnt'] > 0:
               csv_string.extend([str(self.record['fn',0]['par_ref']), str(self.record['fn',0]['par_seq'])])
          else:
               csv_string.extend(['NoParent', 'NoParent'])
                
          if self.record['fncnt'] > 0 and 'si' in self.record:
               #filenameBuffer = [FNrecord['name'], str(self.record['si']['crtime'].dtstr),
               filenameBuffer = [self.record['filename'], str(self.record['si']['crtime'].dtstr),
                          self.record['si']['mtime'].dtstr, self.record['si']['atime'].dtstr, self.record['si']['ctime'].dtstr,
                          self.record['fn',0]['crtime'].dtstr, self.record['fn',0]['mtime'].dtstr,
                          self.record['fn',0]['atime'].dtstr, self.record['fn',0]['ctime'].dtstr]
          elif 'si' in self.record:
               filenameBuffer = ['NoFNRecord', str(self.record['si']['crtime'].dtstr),
                          self.record['si']['mtime'].dtstr, self.record['si']['atime'].dtstr, self.record['si']['ctime'].dtstr,
                          'NoFNRecord', 'NoFNRecord', 'NoFNRecord','NoFNRecord']
          else:
               filenameBuffer = ['NoFNRecord', 'NoSIRecord', 'NoSIRecord', 'NoSIRecord', 'NoSIRecord',
                          'NoFNRecord', 'NoFNRecord', 'NoFNRecord','NoFNRecord']
              
  
          csv_string.extend(filenameBuffer)
        
          if 'objid' in self.record:
               objidBuffer = [self.record['objid']['objid'].objstr, self.record['objid']['orig_volid'].objstr,
                           self.record['objid']['orig_objid'].objstr, self.record['objid']['orig_domid'].objstr]
          else:
               objidBuffer = ['','','','']
  
          csv_string.extend(objidBuffer)                           
  
          # If this goes above four FN attributes, the number of columns will exceed the headers        
          for i in range(1, self.record['fncnt']):
               filenameBuffer = [self.record['fn',i]['name'], self.record['fn',i]['crtime'].dtstr, self.record['fn',i]['mtime'].dtstr,
                          self.record['fn',i]['atime'].dtstr, self.record['fn',i]['ctime'].dtstr]
               csv_string.extend(filenameBuffer)
               filenameBuffer = ''
  
          # Pad out the remaining FN columns
          if self.record['fncnt'] < 2:
               tmp_string = ['','','','','','','','','','','','','','','']
          elif self.record['fncnt'] == 2:
               tmp_string = ['','','','','','','','','','']
          elif self.record['fncnt'] == 3:
               tmp_string = ['','','','','']
            
          csv_string.extend(tmp_string)
     
          # One darned big if statement, alas.
          csv_string.append('True') if 'si' in self.record else csv_string.append('False')
          csv_string.append('True') if 'al' in self.record else csv_string.append('False')
          csv_string.append('True') if self.record['fncnt'] > 0 else csv_string.append('False')
          csv_string.append('True') if 'objid' in self.record else csv_string.append('False')
          csv_string.append('True') if 'volname' in self.record else csv_string.append('False')
          csv_string.append('True') if 'volinfo' in self.record else csv_string.append('False')
          csv_string.append('True') if 'data' in self.record else csv_string.append('False')
          csv_string.append('True') if 'indexroot' in self.record else csv_string.append('False')
          csv_string.append('True') if 'indexallocation' in self.record else csv_string.append('False')
          csv_string.append('True') if 'bitmap' in self.record else csv_string.append('False')
          csv_string.append('True') if 'reparse' in self.record else csv_string.append('False')
          csv_string.append('True') if 'eainfo' in self.record else csv_string.append('False')
          csv_string.append('True') if 'ea' in self.record else csv_string.append('False')
          csv_string.append('True') if 'propertyset' in self.record else csv_string.append('False')
          csv_string.append('True') if 'loggedutility' in self.record else csv_string.append('False')            
        
        
          if 'notes' in self.record:                        # Log of abnormal activity related to this record
               csv_string.append(self.record['notes'])
          else:
               csv_string.append('None')
               self.record['notes'] = ''
          
          if 'stf-fn-shift' in self.record:
               csv_string.append('Y')
          else:
               csv_string.append('N')
  
          if 'usec-zero' in self.record:
               csv_string.append('Y')
          else:
               csv_string.append('N')        
          
          return csv_string

     # MD5|name|inode|mode_as_string|UID|GID|size|atime|mtime|ctime|crtime   
     def mft_to_body(self, full, std):
          ' Return a MFT record in bodyfile format'

     # Add option to use STD_INFO
          
          if self.record['fncnt'] > 0:
          
               if full == True: # Use full path
                    name = self.record['filename']
               else:
                    name = self.record['fn',0]['name']
                    
               if std == True:     # Use STD_INFO
                    rec_bodyfile = ("%s|%s|%s|%s|%s|%s|%s|%d|%d|%d|%d\n" %
                                   ('0',name,'0','0','0','0',
                                   int(self.record['fn',0]['real_fsize']),
                                   int(self.record['si']['atime'].unixtime),  # was str ....
                                   int(self.record['si']['mtime'].unixtime),
                                   int(self.record['si']['ctime'].unixtime),
                                   int(self.record['si']['ctime'].unixtime)))
               else:               # Use FN
                    rec_bodyfile = ("%s|%s|%s|%s|%s|%s|%s|%d|%d|%d|%d\n" %
                                   ('0',name,'0','0','0','0',
                                   int(self.record['fn',0]['real_fsize']),
                                   int(self.record['fn',0]['atime'].unixtime),
                                   int(self.record['fn',0]['mtime'].unixtime),
                                   int(self.record['fn',0]['ctime'].unixtime),
                                   int(self.record['fn',0]['crtime'].unixtime)))
     
          else:
               if 'si' in self.record:
                    rec_bodyfile = ("%s|%s|%s|%s|%s|%s|%s|%d|%d|%d|%d\n" %
                                   ('0','No FN Record','0','0','0','0', '0',
                                   int(self.record['si']['atime'].unixtime),  # was str ....
                                   int(self.record['si']['mtime'].unixtime),
                                   int(self.record['si']['ctime'].unixtime),
                                   int(self.record['si']['ctime'].unixtime)))
               else:
                    rec_bodyfile = ("%s|%s|%s|%s|%s|%s|%s|%d|%d|%d|%d\n" %
                                        ('0','Corrupt Record','0','0','0','0', '0',0, 0, 0, 0))
          
          return (rec_bodyfile)
          
     # l2t CSV output support
     # date,time,timezone,MACB,source,sourcetype,type,user,host,short,desc,version,filename,inode,notes,format,extra
     # http://code.google.com/p/log2timeline/wiki/l2t_csv

     def mft_to_l2t(self):
          ' Return a MFT record in l2t CSV output format'
               
          if self.record['fncnt'] > 0:
               for i in ('atime', 'mtime', 'ctime', 'crtime'):
                    (date,time) = self.record['fn',0][i].dtstr.split(' ')
               
                    if i == 'atime':
                         type_str = '$FN [.A..] time'
                         macb_str = '.A..'
                    if i == 'mtime':
                         type_str = '$FN [M...] time'
                         macb_str = 'M...'
                    if i == 'ctime':
                         type_str = '$FN [..C.] time'
                         macb_str = '..C.'
                    if i == 'crtime':
                         type_str = '$FN [...B] time'
                         macb_str = '...B'
                         
                    csv_string = ("%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s\n" %
                         (date, time, 'TZ', macb_str, 'FILE', 'NTFS $MFT', type_str, 'user', 'host', self.record['filename'], 'desc',
                          'version', self.record['filename'], self.record['seq'], self.record['notes'], 'format', 'extra'))
          
          elif 'si' in self.record:
               for i in ('atime', 'mtime', 'ctime', 'crtime'):
                    (date,time) = self.record['si'][i].dtstr.split(' ')
               
                    if i == 'atime':
                         type_str = '$SI [.A..] time'
                         macb_str = '.A..'
                    if i == 'mtime':
                         type_str = '$SI [M...] time'
                         macb_str = 'M...'
                    if i == 'ctime':
                         type_str = '$SI [..C.] time'
                         macb_str = '..C.'
                    if i == 'crtime':
                         type_str = '$SI [...B] time'
                         macb_str = '...B'
                         
                    csv_string = ("%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s\n" %
                         (date, time, 'TZ', macb_str, 'FILE', 'NTFS $MFT', type_str, 'user', 'host', self.record['filename'], 'desc',
                          'version', self.record['filename'], self.record['seq'], self.record['notes'], 'format', 'extra'))
          
          else:
               csv_string = ("%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s\n" %
                         ('-', '-', 'TZ', 'unknown time', 'FILE', 'NTFS $MFT', 'unknown time', 'user', 'host', 'Corrupt Record', 'desc',
                         'version', 'NoFNRecord', self.record['seq'], '-', 'format', 'extra'))
                            
          return csv_string
     
     
     def add_note(self, s):
          if self.record['notes'] == '':
               self.record['notes'] = "%s" % s
          else:
               self.record['notes'] = "%s | %s |" % (self.mft_record['notes'], s)
               
             
     def decodeMFTHeader(self, raw_record):
     
          self.record['magic'] = struct.unpack("<I", raw_record[:4])[0]
          self.record['upd_off'] = struct.unpack("<H",raw_record[4:6])[0]
          self.record['upd_cnt'] = struct.unpack("<H",raw_record[6:8])[0]
          self.record['lsn'] = struct.unpack("<d",raw_record[8:16])[0]
          self.record['seq'] = struct.unpack("<H",raw_record[16:18])[0]
          self.record['link'] = struct.unpack("<H",raw_record[18:20])[0]
          self.record['attr_off'] = struct.unpack("<H",raw_record[20:22])[0]
          self.record['flags'] = struct.unpack("<H", raw_record[22:24])[0]
          self.record['size'] = struct.unpack("<I",raw_record[24:28])[0]
          self.record['alloc_sizef'] = struct.unpack("<I",raw_record[28:32])[0]
          self.record['base_ref'] = struct.unpack("<Lxx",raw_record[32:38])[0]
          self.record['base_seq'] = struct.unpack("<H",raw_record[38:40])[0]
          self.record['next_attrid'] = struct.unpack("<H",raw_record[40:42])[0]
          self.record['f1'] = raw_record[42:44]                            # Padding
          self.record['recordnum'] = struct.unpack("<I", raw_record[44:48])[0]  # Number of this MFT Record
          self.record['fncnt'] = 0                              # Counter for number of FN attributes
          
     def decodeMFTmagic(self):
         
          if self.record['magic'] == 0x454c4946:
              return "Good"
          elif self.record['magic'] == 0x44414142:
              return 'Bad'
          elif self.record['magic'] == 0x00000000:
              return 'Zero'
          else:
              return 'Unknown'
     
     # decodeMFTisactive and decodeMFTrecordtype both look at the flags field in the MFT header.
     # The first bit indicates if the record is active or inactive. The second bit indicates if it
     # is a file or a folder.
     #
     # I had this coded incorrectly initially. Spencer Lynch identified and fixed the code. Many thanks!
     
     def decodeMFTisactive(self):
          if self.record['flags'] & 0x0001:
               return 'Active'
          else:
               return 'Inactive'
         
     def decodeMFTrecordtype(self):
          tmpBuffer = int(self.record['flags'])
          if int(self.record['flags']) & 0x0002:
               tmpBuffer = 'Folder'
          else:
               tmpBuffer = 'File'
          if int(self.record['flags']) & 0x0004:
               tmpBuffer = "%s %s" % (tmpBuffer, '+ Unknown1')
          if int(self.record['flags']) & 0x0008:
               tmpBuffer = "%s %s" % (tmpBuffer, '+ Unknown2')
     
          return tmpBuffer
         
     def decodeATRHeader(self,s):
         
          d = {}
          d['type'] = struct.unpack("<L",s[:4])[0]
          if d['type'] == 0xffffffff:
              return d
          d['len'] = struct.unpack("<L",s[4:8])[0]
          d['res'] = struct.unpack("B",s[8])[0]
          d['nlen'] = struct.unpack("B",s[9])[0]                  # This name is the name of the ADS, I think.
          d['name_off'] = struct.unpack("<H",s[10:12])[0]
          d['flags'] = struct.unpack("<H",s[12:14])[0]
          d['id'] = struct.unpack("<H",s[14:16])[0]
          if d['res'] == 0:
              d['ssize'] = struct.unpack("<L",s[16:20])[0]
              d['soff'] = struct.unpack("<H",s[20:22])[0]
              d['idxflag'] = struct.unpack("<H",s[22:24])[0]
          else:
              d['start_vcn'] = struct.unpack("<d",s[16:24])[0]
              d['last_vcn'] = struct.unpack("<d",s[24:32])[0]
              d['run_off'] = struct.unpack("<H",s[32:34])[0]
              d['compusize'] = struct.unpack("<H",s[34:36])[0]
              d['f1'] = struct.unpack("<I",s[36:40])[0]
              d['alen'] = struct.unpack("<d",s[40:48])[0]
              d['ssize'] = struct.unpack("<d",s[48:56])[0]
              d['initsize'] = struct.unpack("<d",s[56:64])[0]
      
          return d
     
     def decodeSIAttribute(self, s):
         
          d = {}
          d['crtime'] = WindowsTime(struct.unpack("<L",s[:4])[0],struct.unpack("<L",s[4:8])[0],self.localtz)
          d['mtime'] = WindowsTime(struct.unpack("<L",s[8:12])[0],struct.unpack("<L",s[12:16])[0],self.localtz)
          d['ctime'] = WindowsTime(struct.unpack("<L",s[16:20])[0],struct.unpack("<L",s[20:24])[0],self.localtz)
          d['atime'] = WindowsTime(struct.unpack("<L",s[24:28])[0],struct.unpack("<L",s[28:32])[0],self.localtz)
          d['dos'] = struct.unpack("<I",s[32:36])[0]          # 4
          d['maxver'] = struct.unpack("<I",s[36:40])[0]       # 4
          d['ver'] = struct.unpack("<I",s[40:44])[0]          # 4
          d['class_id'] = struct.unpack("<I",s[44:48])[0]     # 4
          d['own_id'] = struct.unpack("<I",s[48:52])[0]       # 4
          d['sec_id'] = struct.unpack("<I",s[52:56])[0]       # 4
          d['quota'] = struct.unpack("<d",s[56:64])[0]        # 8
          d['usn'] = struct.unpack("<d",s[64:72])[0]          # 8 - end of date to here is 40
       
          return d
     
     def decodeFNAttribute(self, s):
         
          hexFlag = False
          # File name attributes can have null dates.
          
          d = {}
          d['par_ref'] = struct.unpack("<Lxx", s[:6])[0]      # Parent reference nummber + seq number = 8 byte "File reference to the parent directory."
          d['par_seq'] = struct.unpack("<H",s[6:8])[0]        # Parent sequence number
          d['crtime'] = WindowsTime(struct.unpack("<L",s[8:12])[0],struct.unpack("<L",s[12:16])[0],self.localtz)
          d['mtime'] = WindowsTime(struct.unpack("<L",s[16:20])[0],struct.unpack("<L",s[20:24])[0],self.localtz)
          d['ctime'] = WindowsTime(struct.unpack("<L",s[24:28])[0],struct.unpack("<L",s[28:32])[0],self.localtz)
          d['atime'] = WindowsTime(struct.unpack("<L",s[32:36])[0],struct.unpack("<L",s[36:40])[0],self.localtz)
          d['alloc_fsize'] = struct.unpack("<q",s[40:48])[0]
          d['real_fsize'] = struct.unpack("<q",s[48:56])[0]
          d['flags'] = struct.unpack("<d",s[56:64])[0]            # 0x01=NTFS, 0x02=DOS
          d['nlen'] = struct.unpack("B",s[64])[0]
          d['nspace'] = struct.unpack("B",s[65])[0]
      
          # The $MFT string is stored as \x24\x00\x4D\x00\x46\x00\x54. Ie, the first character is a single
          # byte and the remaining characters are two bytes with the first byte a null.
          # Note: Actually, it can be stored in several ways and the nspace field tells me which way.
          #
          # I found the following:
          # 
          # NTFS allows any sequence of 16-bit values for name encoding (file names, stream names, index names,
          # etc.). This means UTF-16 codepoints are supported, but the file system does not check whether a
          # sequence is valid UTF-16 (it allows any sequence of short values, not restricted to those in the
          # Unicode standard).
          #
          # If true, lovely. But that would explain what I am seeing.
          #
          # I just ran across an example of "any sequence of ..." - filenames with backspaces and newlines
          # in them. Thus, the "isalpha" check. I really need to figure out how to handle Unicode better.
          
          if (unicodeHack):
              d['name'] = ''
              for i in range(66, 66 + d['nlen']*2):    
                  if s[i] != '\x00':                         # Just skip over nulls
                     if s[i] > '\x1F' and s[i] < '\x80':          # If it is printable, add it to the string
                          d['name'] = d['name'] + s[i]
                     else:
                          d['name'] = "%s0x%02s" % (d['name'], s[i].encode("hex"))
                          hexFlag = True
      
          # This statement produces a valid unicode string, I just cannot get it to print correctly
          # so I'm temporarily hacking it with the if (unicodeHack) above.
          else:
              d['name'] = s[66:66+d['nlen']*2]
              
      # This didn't work
      #    d['name'] = struct.pack("\u    
      #    for i in range(0, d['nlen']*2, 2):
      #        d['name']=d['name'] + struct.unpack("<H",s[66+i:66+i+1])
              
      # What follows is ugly. I'm trying to deal with the filename in Unicode and not doing well.
      # This solution works, though it is printing nulls between the characters. It'll do for now.
      #    d['name'] = struct.unpack("<%dH" % (int(d['nlen'])*2),s[66:66+(d['nlen']*2)])
      #    d['name'] = s[66:66+(d['nlen']*2)]
      #    d['decname'] = unicodedata.normalize('NFKD', d['name']).encode('ASCII','ignore')
      #    d['decname'] = unicode(d['name'],'iso-8859-1','ignore')
      
          if hexFlag:
              self.add_note('Filename - chars converted to hex')
                
          return d
     
     def decodeAttributeList(self, s):
     
          hexFlag = False
          
          d = {}
          d['type'] = struct.unpack("<I",s[:4])[0]                # 4
          d['len'] = struct.unpack("<H",s[4:6])[0]                # 2
          d['nlen'] = struct.unpack("B",s[6])[0]                  # 1
          d['f1'] = struct.unpack("B",s[7])[0]                    # 1
          d['start_vcn'] = struct.unpack("<d",s[8:16])[0]         # 8
          d['file_ref'] = struct.unpack("<Lxx",s[16:22])[0]       # 6
          d['seq'] = struct.unpack("<H",s[22:24])[0]              # 2
          d['id'] = struct.unpack("<H",s[24:26])[0]               # 4
          if (unicodeHack):
               d['name'] = ''
               for i in range(26, 26 + d['nlen']*2):
                    if s[i] != '\x00':                         # Just skip over nulls
                         if s[i] > '\x1F' and s[i] < '\x80':          # If it is printable, add it to the string
                              d['name'] = d['name'] + s[i]
                         else:
                              d['name'] = "%s0x%02s" % (d['name'], s[i].encode("hex"))
                              hexFlag = True
          else:
               d['name'] = s[26:26+d['nlen']*2]
      
          if hexFlag:
               self.add_note('Filename - chars converted to hex')
               
          return d
     
     def decodeVolumeInfo(self, s):
     
          d = {}
          d['f1'] = struct.unpack("<d",s[:8])[0]                  # 8
          d['maj_ver'] = struct.unpack("B",s[8])[0]               # 1
          d['min_ver'] = struct.unpack("B",s[9])[0]               # 1
          d['flags'] = struct.unpack("<H",s[10:12])[0]            # 2
          d['f2'] = struct.unpack("<I",s[12:16])[0]               # 4
      
          if (self.debug):
              print "+Volume Info"
              print "++F1%d" % d['f1']
              print "++Major Version: %d" % d['maj_ver']
              print "++Minor Version: %d" % d['min_ver']
              print "++Flags: %d" % d['flags']
              print "++F2: %d" % d['f2']
              
          return d
      
     def decodeObjectID(self, s):
     
          d = {}
          d['objid'] = self.ObjectID(s[0:16])
          d['orig_volid'] = self.ObjectID(s[16:32])
          d['orig_objid'] = self.ObjectID(s[32:48])
          d['orig_domid'] = self.ObjectID(s[48:64])
          
          return d
     
     class ObjectID:
          def __init__(self, s):
              self.objid = s
              if s == 0:
                  self.objstr = 'Undefined'
              else:
                  self.objstr = self.FmtObjectID()
      
          def FmtObjectID(self):
              string = "%s-%s-%s-%s-%s" % (binascii.hexlify(self.objid[0:4]),binascii.hexlify(self.objid[4:6]),
                   binascii.hexlify(self.objid[6:8]),binascii.hexlify(self.objid[8:10]),binascii.hexlify(self.objid[10:16]))
                  
              return string



if __name__=="__main__":
    
    session = MftSession()
    session.options = mft_options()
    session.open_files()
    session.process_mft_file()
    session.print_records()
    


     