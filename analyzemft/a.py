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

VERSION='1.16'

SIAttributeSizeXP = 72
SIAttributeSizeNT = 48


class MftSession:
    'Class to describe an entire MFT processing session'

    def __init__(self):
        self.mft = {}
        self.num_records = 0
        
    def open_files(self):
        if (self.options.version == True):
            print("Version is: %s" % (VERSION))
            sys.exit()

        if self.options.filename == None:
            print "-f <filename> required."
            sys.exit()
        
        if self.options.output == None and self.options.bodyfile == None:
            print "-o <filename> or -b <filename> required."
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
            
            self.file_csv.writerow(['Record Number', 'Good', 'Active', 'Record type',
                                    # $Logfile Seq. Num.',
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
                                    'Property Set', 'Logged Utility Stream', 'Log/Notes', 'STF FN Shift', 'uSec Zero'])
    
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
        
        # 1024 is valid for current version of Windows but should really get this value from somewhere         
        raw_record = self.file_mft.read(1024)
        
        while raw_record != "":
            
            self.num_records = self.num_records + 1
            tmp_record = MftRecord()
            tmp_record.debug = self.options.debug
            tmp_record.localtz = self.options.localtz
            tmp_record.parse_record(raw_record)
            print tmp_record.record
            self.mft[tmp_record.record['recordnum']] = tmp_record.record
            

            # ToDo - generate filepath
            
            if self.num_records > 10:
                sys.exit()
            
            raw_record = self.file_mft.read(1024)
    
    def gen_filepaths(self):
        
           if ( mft_record['fncnt'] > 0 ):
                mft_record['filename'] = ''
                buildingBlockFolder = getFolderPath( mft_record['fn',mft_record['fncnt']-1]['par_ref'] )
                mft_record['filename'] = mft_record['filename'] + '/' + mft_record['fn',mft_record['fncnt']-1]['name']
                mft_record['filename'] = mft_record['filename'].replace('//','/')
                if options.debug: print "Filename (with path): %s" % mft_record['filename']


    
class MftRecord:
    'Common base class for all MFT records'

    def __init__(self):
        self.record = {}
        self.record['filepath'] = "NotCalculated"

    def parse_record(self, rec):
        
        self.raw_record = rec
        self.decodeMFTHeader();
        
        record_number = self.record['recordnum']
       
        if self.debug:
            print '-->Record number: %d\n\tMagic: %s Attribute offset: %d Flags: %s Size:%d' % (record_number, self.record['magic'],
                self.record['attr_off'], hex(int(self.record['flags'])), self.record['size'])        
        
        if self.record['magic'] == 0x44414142:
            if self.debug:
                print "BAAD MFT Record"
            self.record['baad'] = True
        
        else:
             
            read_ptr = self.record['attr_off']
                 
            while (read_ptr < 1024):
             
                ATRrecord = self.decodeATRHeader(self.raw_record[read_ptr:])
                if ATRrecord['type'] == 0xffffffff:             # End of attributes
                    break
             
                if self.debug:
                    print "Attribute type: %x Length: %d Res: %x" % (ATRrecord['type'], ATRrecord['len'], ATRrecord['res'])
         
                if ATRrecord['type'] == 0x10:                   # Standard Information
                    if self.debug:
                        print "Stardard Information:\n++Type: %s Length: %d Resident: %s Name Len:%d Name Offset: %d" % \
                            (hex(int(ATRrecord['type'])),ATRrecord['len'],ATRrecord['res'],ATRrecord['nlen'],ATRrecord['name_off'])
                    SIrecord = self.decodeSIAttribute(self.raw_record[read_ptr+ATRrecord['soff']:])
                    self.record['si'] = SIrecord
                    if self.debug:
                        print "++CRTime: %s\n++MTime: %s\n++ATime: %s\n++EntryTime: %s" % \
                            (SIrecord['crtime'].dtstr, SIrecord['mtime'].dtstr, SIrecord['atime'].dtstr, SIrecord['ctime'].dtstr)
                 
                elif ATRrecord['type'] == 0x20:                 # Attribute list
                    if self.debug:
                        print "Attribute list"
                    if ATRrecord['res'] == 0:
                        ALrecord = self.decodeAttributeList(self.raw_record[ReadPtr+ATRrecord['soff']:])
                        self.record['al'] = ALrecord
                        if self.debug:
                            print "Name: %s"  % (ALrecord['name'])
                    else:
                        if self.debug:
                            print "Non-resident Attribute List?"
                        self.record['al'] = None
                         
                elif ATRrecord['type'] == 0x30:                 # File name
                    if self.debug: print "File name record"
                    FNrecord = self.decodeFNAttribute(self.raw_record[read_ptr+ATRrecord['soff']:])
                    self.record['fn',self.record['fncnt']] = FNrecord
                    if self.debug: print "Name: %s (%d)" % (FNrecord['name'],self.record['fncnt'])
                    self.record['fncnt'] = self.record['fncnt'] + 1
                    if FNrecord['crtime'] != 0:
                        if options.debug: print "\tCRTime: %s MTime: %s ATime: %s EntryTime: %s" % (FNrecord['crtime'].dtstr,
                                FNrecord['mtime'].dtstr, FNrecord['atime'].dtstr, FNrecord['ctime'].dtstr)
         
                elif ATRrecord['type'] == 0x40:                 #  Object ID
                    ObjectIDRecord = self.decodeObjectID(self.raw_record[ReadPtr+ATRrecord['soff']:])
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
                    VolumeInfoRecord = self.decodeVolumeInfo(self.raw_record[read_ptr+ATRrecord['soff']:])
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
  
 
                        
     
    def mft_to_csv(self):
        print "write a record to a CSV file"
        
    def mft_to_body(self, fd):
        print "write a record to a body file"
        
    def add_note(s):     
        if 'notes' in self.mft_record:
            self.mft_record['notes'] = "%s | %s |" % (self.mft_record['notes'], s)
        else:
            self.mft_record['notes'] = "%s" % s
            
            
    def decodeMFTHeader(self):
    
        self.record['magic'] = struct.unpack("<I", self.raw_record[:4])[0]
        self.record['upd_off'] = struct.unpack("<H",self.raw_record[4:6])[0]
        self.record['upd_cnt'] = struct.unpack("<H",self.raw_record[6:8])[0]
        self.record['lsn'] = struct.unpack("<d",self.raw_record[8:16])[0]
        self.record['seq'] = struct.unpack("<H",self.raw_record[16:18])[0]
        self.record['link'] = struct.unpack("<H",self.raw_record[18:20])[0]
        self.record['attr_off'] = struct.unpack("<H",self.raw_record[20:22])[0]
        self.record['flags'] = struct.unpack("<H", self.raw_record[22:24])[0]
        self.record['size'] = struct.unpack("<I",self.raw_record[24:28])[0]
        self.record['alloc_sizef'] = struct.unpack("<I",self.raw_record[28:32])[0]
        self.record['base_ref'] = struct.unpack("<Lxx",self.raw_record[32:38])[0]
        self.record['base_seq'] = struct.unpack("<H",self.raw_record[38:40])[0]
        self.record['next_attrid'] = struct.unpack("<H",self.raw_record[40:42])[0]
        self.record['f1'] = self.raw_record[42:44]                            # Padding
        self.record['recordnum'] = struct.unpack("<I", self.raw_record[44:48])[0]  # Number of this MFT Record
        self.record['fncnt'] = 0                              # Counter for number of FN attributes
        
    def decodeMFTmagic(s):
        if s == 0x454c4946:
            return "Good"
        elif s == 0x44414142:
            return 'Bad'
        elif s == 0x00000000:
            return 'Zero'
        else:
            return 'Unknown'
    
    # decodeMFTisactive and decodeMFTrecordtype both look at the flags field in the MFT header.
    # The first bit indicates if the record is active or inactive. The second bit indicates if it
    # is a file or a folder.
    #
    # I had this coded incorrectly initially. Spencer Lynch identified and fixed the code. Many thanks!
    
    def decodeMFTisactive(s):
        if s & 0x0001:
            return 'Active'
        else:
            return 'Inactive'
        
    def decodeMFTrecordtype(s):
         tmpBuffer = s
         if s & 0x0002:
            tmpBuffer = 'Folder'
         else:
              tmpBuffer = 'File'
         if s & 0x0004:
              tmpBuffer = "%s %s" % (tmpBuffer, '+ Unknown1')
         if s & 0x0008:
              tmpBuffer = "%s %s" % (tmpBuffer, '+ Unknown2')
    
         return tmpBuffer
    

        
    def decodeATRHeader(self,s):
        
        d = {}
        
        d['type'] = struct.unpack("<L",s[:4])[0]
        if d['type'] == 0xffffffff:
            return d
        d['len'] = struct.unpack("<L",self.raw_record[4:8])[0]
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
              addNote('Filename - chars converted to hex')
              
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
              addNote('Filename - chars converted to hex')
              
         return d
    
    def decodeVolumeInfo(self, s):
    
        d = {}
        d['f1'] = struct.unpack("<d",s[:8])[0]                  # 8
        d['maj_ver'] = struct.unpack("B",s[8])[0]               # 1
        d['min_ver'] = struct.unpack("B",s[9])[0]               # 1
        d['flags'] = struct.unpack("<H",s[10:12])[0]            # 2
        d['f2'] = struct.unpack("<I",s[12:16])[0]               # 4
    
        if (options.debug):
            print "+Volume Info"
            print "++F1%d" % d['f1']
            print "++Major Version: %d" % d['maj_ver']
            print "++Minor Version: %d" % d['min_ver']
            print "++Flags: %d" % d['flags']
            print "++F2: %d" % d['f2']
            
        return d
    
    def decodeObjectID(self, s):
    
        d = {}
        d['objid'] = ObjectID(s[0:16])
        d['orig_volid'] = ObjectID(s[16:32])
        d['orig_objid'] = ObjectID(s[32:48])
        d['orig_domid'] = ObjectID(s[48:64])
        
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
    


     