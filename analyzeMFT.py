#!/usr/bin/env python

# Author: David Kovar [dkovar <at> gmail [dot] com]
# Name: analyzeMFT.py
#
# Copyright (c) 2010 David Kovar. All rights reserved.
# This software is distributed under the Common Public License 1.0
#
# Date: May 2011
#


'''
OOP approach:


PreProcessing

- Module based
    1) Get timezone and hostname
    2) Get list of users
    3) .....
    
Then read in $MFT

Then module based output.



Documentation

Usage: analyzeMFT.py [options]

Options:
  -h, --help            show this help message and exit
  -f FILE, --file=FILE  read MFT from FILE
  -o FILE, --output=FILE
                        write results to FILE
  -a, --anomaly         turn on anomaly detection
  -b FILE, --bodyfile=FILE
                        write MAC information to bodyfile
  -g, --gui             Use GUI for file selection
  -d, --debug           turn on debugging output


You can turn off all the GUI dependencies by setting the noGUI flag to 'True'. This is for installations
that don't want to install the tk/tcl libraries.

Version 1.0: Initial release
Version 1.1: Split parent folder reference and sequence into two fields. I'm still trying to figure out the
             significance of the parent folder sequence number, but I'm convinced that what some documentation
             refers to as the parent folder record number is really two values - the parent folder record number
             and the parent folder sequence number. 
Version 1.2: Fixed problem with non-printable characters in filenames. Any Unicode character is legal in a
             filename, including newlines. This presented some problems in my output. Characters that do not
             render well are now converted to hex and a note is added to the Notes column indicating this.
             (I've learned a lot about Unicode since I first wrote this.)
             Added "compile time" flag to turn off the inclusion of any GUI related modules and libraries
             for systems missing tk/tcl support. (Set noGUI to True in the code)
Version 1.3: Added new column to hold log entries relating to each record. For example, a note stating that
             some characters in the filename were converted to hex as they could not be printed.
Version 1.4: Credit: Spencer Lynch. I was misusing the flags field in the MFT header. The first bit is
             Active/Inactive. The second bit is File/Folder. 
Version 1.5: Fixed date/time reporting. I wasn't reporting useconds at all.
             Added anomaly detection. Adds two columns:
                    std-fn-shift:  If Y, entry's FN create time is after the STD create time
                    usec-zero: If Y, entry's STD create time's usec value is zero
Version 1.6: Various bug fixes
Version 1.7: Bodyfile support, with thanks to Dave Hull
Version 1.8: Added support for full path extraction, written by Kristinn Gudjonsson
Version 1.9: Added support for csv timeline output
                    
Purpose:

analyzeMFT.py is designed to fully parse the MFT file from an NTFS filesystem
and present the results as accurately as possible in a format that allows
further analysis with other tools. At present, it will read an entire MFT
through to the end without error, but it skips over parsing some of the
attributes. These will be filled in as time permits.

Caution:

This code is very much under development. You should not depend on its results without double checking
them against at least one other tool.

Output:

The output is currently written in CSV format. Due to the fact that Excel
automatically determines the type of data in a column, it is recommended that
you write the output to a file without the .csv extension, open it in Excel, and
set all the columns to "Text" rather than "General" when the import wizard
starts. Failure to do so will result in Excel formatting the columns in a way
that misrepresents the data.

I could pad the data in such a way that forces Excel to set the column type correctly
but this might break other tools.

Inspiration:

My original inspiration was a combination of MFT Ripper (thus the current output format) and the
SANS 508.1 study guide. I couldn't bear to read about NTFS structures again,
particularly since the information didn't "stick". I also wanted to learn Python
so I figured that using it to tear apart the MFT file was a reasonably sized
project.

Many of the variable names are taken directly from Brian Carrier's The Sleuth Kit. His code, plus his
book "File System Forensic Analysis", was very helpful in my efforts to write this code.

The output format is almost identical to Mark Menz's MFT Ripper. His tool really inspired me to learn
more about the structure of the MFT and to learn what additional information I could glean from
the data.

I also am getting much more interested in timeline analysis and figured that really understanding the
the MFT and having a tool that could parse it might serve as a good foundation
for further research in that area.

Limitations:

Future work:

1) Figure out how to write the CSV file in a manner that forces Excel to interpret the date/time
fields as text. If you add the .csv extension Excel will open the file without invoking the import
wizard and the date fields are treated as "General" and the date is chopped leaving just the time.
2) Add version switch
3) Add "mftr" switch - produce MFT Ripper compatible output
4) Add "extract" switch - extract or work on live MFT file
5) Finish parsing all possible attributes
6) Look into doing more timeline analysis with the information
7) Improve the documentation so I can use the structures as a reference and reuse the code more effectively
8) Clean up the code and, in particular, follow standard naming conventions
9) There are two MFT entry flags that appear that I can't determine the significance of. These appear in
    the output as Unknown1 and Unknown2
10) Parse filename based on 'nspace' value in FN structure
11) Test it and ensure that it works on all major Windows OS versions
12) Output HTML as well as CSV
13) If you specify a bad input filename and a good output filename, you get an
error about the output filename.


See other ToDos in the code

Useful Documentation:

1) http://data.linux-ntfs.org/ntfsdoc.pdf


Malware analysis notes:

I don't have access to the examples right now but I have found malware that uses the same MAC times of the legitimate files it is trying to mask itself as. For example I have found malicious ccapp.exe files in system32 Dir with the same dates and times as the real ccapp.exe that reside in the Symantec folder. 

Maybe you can look for files with same names that have same SIA times but different FNA times in MFT?  

Just an idea.   

Dave Nardoni

---

1.  win32api can only update STDINFO times.  As far as I know, there is no win32api ability to update FN times directly.  
2.  Nanoseconds fields will most likely be zero as a result of file backdating.  There are many files that also have this,
    however, you have data reduction of about 99%.  You would then process and compare FN Birthdates compared to STDINFO
    Birthdates.
3.  No natural capabilities exist on windows to backdate files with the exception of powershell.  (no "touch" equiv).
    Capability would have to be written or downloaded to get it to backdate.
4.  Take a look at the following http://blogs.sans.org/computer-forensics/2010/04/12/windows-7-mft-entry-timestamp-properties/
    for more timestamp info.
5.  FN times will most likely not be backdated.  So look for FN times in the future... especially the "creation" time compared
    to the STF creation time.

Best,
Rob

---

A good example can be found from Lance Mueller, here:
http://www.forensickb.com/2009/02/detecting-timestamp-changing-utlities.html

In short, if files are "touched", or "timestomped", the $SIA timestamps are modified but the $FNA timestamps are not. When
working malware cases, many times the installation routine will either 'stomp' the times of the malware, or copy them from
a legitimate file. Using this sort of comparison is a great way to find malware.

At this point, I've used "timestomp" in a general sense. I've read research that indicates that there are some malware
utilities for Windows systems that perform the 'stomping', but they do so with a 32-bit (vice 64-bit) resolution. In such
cases, the upper half of the time value would be all 0's. In Perl (I know you use Python), a check for this would look
something like "if (unpack("V",$high) == 0)".

In addition to the modification of the file times, I would also consider the location of the files themselves, particularly
any DLLs. The DLL Search Order issue that came up publicly this summer, but had been known for at least 10 yrs prior to that...

Harlan

---

Bodyfile:

MD5|name|inode|mode_as_string|UID|GID|size|atime|mtime|ctime|crtime

The times are reported in UNIX time format. Lines that start with '#' are ignored and treated as comments.
In mactime, many of theses fields are optional. Its only requirement is that at least one of the time values
is non-zero. The non-time values are simply printed as is. Other tools that read this file format may have
different requirements.

Source: http://wiki.sleuthkit.org/index.php?title=Body_file

---

Mountpoint/full path:

@dckovar In fls, user provides mount point (i.e. C:), fls appends full path after that, so yeah, full path would be helpful.

David it was not my intention for you to have to do this, but I'm glad you're taking on the challenge. :-)

Here's what I was thinking of, currently with fls I can do:

fls -m C: <img> > bodyfile

mactime -b bodyfile -d -m -y > timeline.csv

And get something like this:

Date,Size,Type,Mode,UID,GID,Meta,File Name
2009 01 15 Thu 01:10:22,451,.a..,r/rrwxrwxrwx,0,0,12888-128-1,C:/Documents and Settings/Donald Blake/Cookies/donald blake@aol[2].txt
2009 01 15 Thu 10:27:09,180224,.a..,r/rrwxrwxrwx,0,0,2143-128-3,C:/WINDOWS/system32/scecli.dll


I'd like to add FN time stamp attributes, doing something like this:

fls -m C:FN <img> > bodyfile

mactime -b bodyfile -d -m -y > timeline.csv

And get something like this:

Date,Size,Type,Mode,UID,GID,Meta,File Name
2009 01 15 Thu 10:27:09,180224,.a..,r/rrwxrwxrwx,0,0,2143-128-3,C:/WINDOWS/system32/scecli.dll
2009 01 15 Thu 10:27:09,180224,.a..,r/rrwxrwxrwx,0,0,2143-128-3,C:FN/WINDOWS/system32/scecli.dll
2009 01 15 Thu 01:11:22,451,.a..,r/rrwxrwxrwx,0,0,12888-128-1,C:/Documents and Settings/Donald Blake/Cookies/donald blake@aol[2].txt
2009 01 15 Fri 11:08:27,451,m...,r/rrwxrwxrwx,0,0,12888-128-1,C:FN/Documents and Settings/Donald Blake/Cookies/donald blake@aol[2].txt


Of course the example above is hypothetical, but you get the idea. My reason for wanting the FN attributes is because currently, 
there are no known tools that modify FN time stamp attributes. Timestomp and PowerShell techniques only mod STDINFO attributes so 
having FN could be useful for cases where time stamp manipulation is suspected.

Dave Hull

'''
noGUI = False                                # This one is for Rob
unicodeHack = True                           # This one is for me

import struct, sys, ctypes, re, time, unicodedata, csv, binascii, os, platform
from datetime import date, datetime
from optparse import OptionParser
# import fnmatch

# Globals

SIAttributeSizeXP = 72
SIAttributeSizeNT = 48


if noGUI == False:
     if platform.system() == "Windows":
          import win32gui

     from Tkinter import *
     import Tkinter as tk
     import tkCommonDialog
     import tkFileDialog
     # from Tkinter.dialog import Dialog
     # from Tkinter import commondialog

class WindowsTime:
    "Convert the Windows time in 100 nanosecond intervals since Jan 1, 1601 to time in seconds since Jan 1, 1970"
    
    def __init__(self, low, high):
        self.low = long(low)
        self.high = long(high)
        
        if (low == 0) and (high == 0):
            self.dt = 0
            self.dtstr = "Not defined"
            self.unixtime = 0
            return
        
        # Windows NT time is specified as the number of 100 nanosecond intervals since January 1, 1601.
        # UNIX time is specified as the number of seconds since January 1, 1970. 
        # There are 134,774 days (or 11,644,473,600 seconds) between these dates.
        self.unixtime = self.GetUnixTime()
              
        try:  
          self.dt = datetime.fromtimestamp(self.unixtime)

          # Pass isoformat a delimiter if you don't like the default "T".
          self.dtstr = self.dt.isoformat(' ')
          
        except:
          self.dt = 0
          self.dtstr = "Invalid timestamp"
          self.unixtime = 0
          
        
    def GetUnixTime(self):
        t=float(self.high)*2**32 + self.low

     # The '//' does a floor on the float value, where *1e-7 does not, resulting in an off by one second error
     # However, doing the floor loses the usecs....
        return (t*1e-7 - 11644473600)
     #return((t//10000000)-11644473600)
     
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

def addNote(s):
     
     if 'notes' in MFTR:
#          MFTR['notes'] = "%s | %s |" % (MFTR['notes'], s)
          MFTR['notes'] = "%s | %s |" % (MFTR['notes'], s)
     else:
          MFTR['notes'] = "%s" % s
          

def decodeMFTHeader(s):

    d = {}

    d['magic'] = struct.unpack("<I", s[:4])[0]
    d['upd_off'] = struct.unpack("<H",s[4:6])[0]
    d['upd_cnt'] = struct.unpack("<H",s[6:8])[0]
    d['lsn'] = struct.unpack("<d",s[8:16])[0]
    d['seq'] = struct.unpack("<H",s[16:18])[0]
    d['link'] = struct.unpack("<H",s[18:20])[0]
    d['attr_off'] = struct.unpack("<H",s[20:22])[0]
    d['flags'] = struct.unpack("<H", s[22:24])[0]
    d['size'] = struct.unpack("<I",s[24:28])[0]
    d['alloc_sizef'] = struct.unpack("<I",s[28:32])[0]
    d['base_ref'] = struct.unpack("<Lxx",s[32:38])[0]
    d['base_seq'] = struct.unpack("<H",s[38:40])[0]
    d['next_attrid'] = struct.unpack("<H",s[40:42])[0]
    d['f1'] = s[42:44]
    d['entry'] = s[44:48]
    d['fncnt'] = 0                              # Counter for number of FN attributes

    return d

def decodeATRHeader(s):
    
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

def decodeSIAttribute(s):
    
    d = {}
    d['crtime'] = WindowsTime(struct.unpack("<L",s[:4])[0],struct.unpack("<L",s[4:8])[0])
    d['mtime'] = WindowsTime(struct.unpack("<L",s[8:12])[0],struct.unpack("<L",s[12:16])[0])
    d['ctime'] = WindowsTime(struct.unpack("<L",s[16:20])[0],struct.unpack("<L",s[20:24])[0])
    d['atime'] = WindowsTime(struct.unpack("<L",s[24:28])[0],struct.unpack("<L",s[28:32])[0])
    d['dos'] = struct.unpack("<I",s[32:36])[0]          # 4
    d['maxver'] = struct.unpack("<I",s[36:40])[0]       # 4
    d['ver'] = struct.unpack("<I",s[40:44])[0]          # 4
    d['class_id'] = struct.unpack("<I",s[44:48])[0]     # 4
    d['own_id'] = struct.unpack("<I",s[48:52])[0]       # 4
    d['sec_id'] = struct.unpack("<I",s[52:56])[0]       # 4
    d['quota'] = struct.unpack("<d",s[56:64])[0]        # 8
    d['usn'] = struct.unpack("<d",s[64:72])[0]          # 8 - end of date to here is 40
 
    return d

def decodeFNAttribute(s):
    
    hexFlag = False
    # File name attributes can have null dates.
    
    d = {}
    d['par_ref'] = struct.unpack("<Lxx", s[:6])[0]      # Parent reference nummber
    d['par_seq'] = struct.unpack("<H",s[6:8])[0]        # Parent sequence number
    d['crtime'] = WindowsTime(struct.unpack("<L",s[8:12])[0],struct.unpack("<L",s[12:16])[0])
    d['mtime'] = WindowsTime(struct.unpack("<L",s[16:20])[0],struct.unpack("<L",s[20:24])[0])
    d['ctime'] = WindowsTime(struct.unpack("<L",s[24:28])[0],struct.unpack("<L",s[28:32])[0])
    d['atime'] = WindowsTime(struct.unpack("<L",s[32:36])[0],struct.unpack("<L",s[36:40])[0])
    d['alloc_fsize'] = struct.unpack("<d",s[40:48])[0]
    d['real_fsize'] = struct.unpack("<d",s[48:56])[0]
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

def decodeAttributeList(s):

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

def decodeVolumeInfo(s):

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

def decodeObjectID(s):

    d = {}
    d['objid'] = ObjectID(s[0:16])
    d['orig_volid'] = ObjectID(s[16:32])
    d['orig_objid'] = ObjectID(s[32:48])
    d['orig_domid'] = ObjectID(s[48:64])
    
    return d

def anomalyDetect():
     
     
     # Check for STD create times that are before the FN create times
     if MFTR['fncnt'] > 0:
#          print MFTR['si']['crtime'].dt, MFTR['fn', 0]['crtime'].dt
          
          try:
               if (MFTR['fn', 0]['crtime'].dt == 0) or (MFTR['si']['crtime'].dt < MFTR['fn', 0]['crtime'].dt):
                    MFTR['stf-fn-shift'] = True
          # This is a kludge - there seem to be some legit files that trigger an exception in the above. Needs to be
          # investigated
          except:
               MFTR['stf-fn-shift'] = True
     
          # Check for STD create times with a nanosecond value of '0'
          if MFTR['fn',0]['crtime'].dt != 0:
               if MFTR['fn',0]['crtime'].dt.microsecond == 0:
                    MFTR['usec-zero'] = True

def buildFolderStructure():
	# 1024 is valid for current version of Windows but should really get this value from somewhere         
	recordNumber = 0
	record = F.read(1024)

	while record != "":
		MFTR = decodeMFTHeader(record);
    
		if MFTR['magic'] == 0x44414142:
			MFTR['baad'] = True
		else:
			ReadPtr = MFTR['attr_off']
              
			while (ReadPtr < 1024):
				ATRrecord = decodeATRHeader(record[ReadPtr:])
				if ATRrecord['type'] == 0xffffffff:             # End of attributes
					break
				elif ATRrecord['type'] == 0x30:                 # File name
					FNrecord = decodeFNAttribute(record[ReadPtr+ATRrecord['soff']:])
					MFTR['fn',MFTR['fncnt']] = FNrecord
					MFTR['fncnt'] = MFTR['fncnt'] + 1

				if ATRrecord['len'] > 0:
					ReadPtr = ReadPtr + ATRrecord['len']
				else:
					break

			# we need to populate the folder structure
			if ( MFTR['fncnt'] > 0 ):
				if ( decodeMFTrecordtype(int(MFTR['flags'])) == 'Folder' ):
					if options.debug: print "Building folder %s (parent %d - rec %d)" % ( MFTR['fn',MFTR['fncnt']-1]['name'], MFTR['fn',MFTR['fncnt']-1]['par_ref'], recordNumber )
					Folders[recordNumber] = {}
					Folders[recordNumber]['parent'] = MFTR['fn',MFTR['fncnt']-1]['par_ref']
					Folders[recordNumber]['name'] = MFTR['fn',MFTR['fncnt']-1]['name']

		record = F.read(1024)
		recordNumber = recordNumber + 1
    

def getFolderPath(p):
	if options.debug: print "Building Folder For Record Number (%d)" % p
	n = ''

	if ( p == 0 ) or ( p == 5 ):
		MFTR['filename'] = '/' + MFTR['filename']
		return 1

        # not the end, so add to the filename
	try:
		n = Folders[p]['name'] + '/' + MFTR['filename']
	except KeyError:
		if options.debug: print "Error while trying to determine path (%s)" % MFTR['filename']
		MFTR['filename'] = '???/' + MFTR['filename']
		return 1

	MFTR['filename'] = n

        # and call the subroutine again
	getFolderPath( Folders[p]['parent'] )
	
	return 1
     
def writeCSVFile():
    
     mftBuffer = ''
     tmpBuffer = ''
     filenameBuffer = ''
    
     if recordNumber == -1:
          # Write headers
          OutFile.writerow(['Record Number', 'Good', 'Active', 'Record type',
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
                         'Property Set', 'Logged Utility Stream', 'Log/Notes', 'STF FN Shift', 'uSec Zero'])
     elif 'baad' in MFTR:
          OutFile.writerow(["%s" % recordNumber,"BAAD MFT Record"])
     else:
          mftBuffer = [recordNumber, decodeMFTmagic(MFTR['magic']), decodeMFTisactive(MFTR['flags']),
                          decodeMFTrecordtype(int(MFTR['flags']))]

#        tmpBuffer = ["%d" % MFTR['lsn']]
#        mftBuffer.extend(tmpBuffer)
          tmpBuffer = ["%d" % MFTR['seq']]
          mftBuffer.extend(tmpBuffer)
        
          if MFTR['fncnt'] > 0:
               mftBuffer.extend([str(MFTR['fn',0]['par_ref']), str(MFTR['fn',0]['par_seq'])])
          else:
               mftBuffer.extend(['NoParent', 'NoParent'])
                
          if MFTR['fncnt'] > 0:
               #filenameBuffer = [FNrecord['name'], str(SIrecord['crtime'].dtstr),
               filenameBuffer = [MFTR['filename'], str(SIrecord['crtime'].dtstr),
                          SIrecord['mtime'].dtstr, SIrecord['atime'].dtstr, SIrecord['ctime'].dtstr,
                          MFTR['fn',0]['crtime'].dtstr, MFTR['fn',0]['mtime'].dtstr,
                          MFTR['fn',0]['atime'].dtstr, MFTR['fn',0]['ctime'].dtstr]
          else:
               # Should replace SIrecord with MFTR['si']
               filenameBuffer = ['NoFNRecord', str(SIrecord['crtime'].dtstr),
                          SIrecord['mtime'].dtstr, SIrecord['atime'].dtstr, SIrecord['ctime'].dtstr,
                          'NoFNRecord', 'NoFNRecord', 'NoFNRecord','NoFNRecord']

          mftBuffer.extend(filenameBuffer)
        
          if 'objid' in MFTR:
               objidBuffer = [MFTR['objid']['objid'].objstr, MFTR['objid']['orig_volid'].objstr,
                           MFTR['objid']['orig_objid'].objstr, MFTR['objid']['orig_domid'].objstr]
          else:
               objidBuffer = ['','','','']

          mftBuffer.extend(objidBuffer)                           

# If this goes above four FN attributes, the number of columns will exceed the headers        
          for i in range(1, MFTR['fncnt']):
               filenameBuffer = [MFTR['fn',i]['name'], MFTR['fn',i]['crtime'].dtstr, MFTR['fn',i]['mtime'].dtstr,
                          MFTR['fn',i]['atime'].dtstr, MFTR['fn',i]['ctime'].dtstr]
               mftBuffer.extend(filenameBuffer)
               filenameBuffer = ''

# Pad out the remaining FN columns
          if MFTR['fncnt'] < 2:
               tmpBuffer = ['','','','','','','','','','','','','','','']
          elif MFTR['fncnt'] == 2:
               tmpBuffer = ['','','','','','','','','','']
          elif MFTR['fncnt'] == 3:
               tmpBuffer = ['','','','','']
            
          mftBuffer.extend(tmpBuffer)

# One darned big if statement, alas.

          mftBuffer.append('True') if 'si' in MFTR else mftBuffer.append('False')
          mftBuffer.append('True') if 'al' in MFTR else mftBuffer.append('False')
          mftBuffer.append('True') if MFTR['fncnt'] > 0 else mftBuffer.append('False')
          mftBuffer.append('True') if 'objid' in MFTR else mftBuffer.append('False')
          mftBuffer.append('True') if 'volname' in MFTR else mftBuffer.append('False')
          mftBuffer.append('True') if 'volinfo' in MFTR else mftBuffer.append('False')
          mftBuffer.append('True') if 'data' in MFTR else mftBuffer.append('False')
          mftBuffer.append('True') if 'indexroot' in MFTR else mftBuffer.append('False')
          mftBuffer.append('True') if 'indexallocation' in MFTR else mftBuffer.append('False')
          mftBuffer.append('True') if 'bitmap' in MFTR else mftBuffer.append('False')
          mftBuffer.append('True') if 'reparse' in MFTR else mftBuffer.append('False')
          mftBuffer.append('True') if 'eainfo' in MFTR else mftBuffer.append('False')
          mftBuffer.append('True') if 'ea' in MFTR else mftBuffer.append('False')
          mftBuffer.append('True') if 'propertyset' in MFTR else mftBuffer.append('False')
          mftBuffer.append('True') if 'loggedutility' in MFTR else mftBuffer.append('False')            
        
          if 'notes' in MFTR:                        # Log of abnormal activity related to this record
               mftBuffer.append(MFTR['notes'])
          else:
               mftBuffer.append('None')
          
          if 'stf-fn-shift' in MFTR:
               mftBuffer.append('Y')
          else:
               mftBuffer.append('N')

          if 'usec-zero' in MFTR:
               mftBuffer.append('Y')
          else:
               mftBuffer.append('N')

          OutFile.writerow(mftBuffer)
        
        
          if options.bodyfile != None:
               # MD5|name|inode|mode_as_string|UID|GID|size|atime|mtime|ctime|crtime
     
               # To do - figure out file size
                    
               if MFTR['fncnt'] > 0:
                    bodyfile.write("%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s\n" %
                                   ('',FNrecord['name'],'0','','0','0','',
                                   MFTR['fn',0]['atime'].unixtime,
                                   MFTR['fn',0]['mtime'].unixtime,
                                   MFTR['fn',0]['ctime'].unixtime,
                                   MFTR['fn',0]['crtime'].unixtime))
               else:
                    bodyfile.write("%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s\n" %
                                   ('','No FN Record','0','','0','0','',
                                   str(SIrecord['atime'].unixtime),
                                   SIrecord['mtime'].unixtime,
                                   SIrecord['ctime'].unixtime,
                                   SIrecord['ctime'].unixtime))
# Get command line options

parser = OptionParser()
parser.set_defaults(debug=False,UseLocalTimezone=False,UseGUI=False)

parser.add_option("-f", "--file", dest="filename",
                  help="read MFT from FILE", metavar="FILE")

# ToDo: implement
#parser.add_option("-l", "--localtimezone",
#                  action="store_true", dest="UseLocalTimezone",
#                  help="set all times to local time rather than UTC")

parser.add_option("-o", "--output", dest="output",
                  help="write results to FILE", metavar="FILE")

parser.add_option("-a", "--anomaly",
                  action="store_true", dest="anomaly",
                  help="turn on anomaly detection")

parser.add_option("-b", "--bodyfile", dest="bodyfile",
                  help="write MAC information to bodyfile", metavar="FILE")

parser.add_option("-c", "--csvtimefile", dest="csvtimefile",
                  help="write CSV format timeline file", metavar="FILE")

if noGUI == False:
     parser.add_option("-g", "--gui",
                       action="store_true", dest="UseGUI",
                       help="Use GUI for file selection")
parser.add_option("-d", "--debug",
                  action="store_true", dest="debug",
                  help="turn on debugging output")

(options, args) = parser.parse_args()

# Start reading file

if (options.UseGUI):
    
    # Hide root tK window
    root = tk.Tk()
    root.withdraw()
    options.filename = tkFileDialog.askopenfilename(title='MFT file to open',filetypes=[("all files", "*")])

    options.output = tkFileDialog.asksaveasfilename(title='Output file')
    
    if options.bodyfile != None:
     options.bodyfile = tkFileDialog.asksaveasfilename(title='bodyfile file')
     
     if options.csvtimefile != None:
          options.bodyfile = tkFileDialog.asksaveasfilename(title='bodyfile file')

else:
    if options.filename == None:
        print "-f <filename> required."
        sys.exit()
    
    if options.output == None:
        print "-o <filename> required."
        sys.exit()
    

try:
    F = open(options.filename, 'rb')
except:
    print "Unable to open file: %s" % options.filename
    sys.exit()

try:
    OutFile = csv.writer(open(options.output, 'wb'), dialect=csv.excel,quoting=1)
except (IOError, TypeError):
    print "Unable to open file: %s" % options.output
    sys.exit()
    
if options.bodyfile != None:
     try:
         bodyfile = open(options.bodyfile, 'w')
     except:
         print "Unable to open file: %s" % options.bodyfile
         sys.exit()
         
if options.csvtimefile != None:
     try:
          csv_time_file = csv.writer(open(options.csvtimefile, 'wb'), dialect=csv.excel,quoting=1)
     except (IOError, TypeError):
          print "Unable to open file: %s" % options.csvtimefile
          sys.exit()
     
# Write the headers to the output file
recordNumber = -1
writeCSVFile()
recordNumber = 0

Folders = {}
MFTR = {}
buildFolderStructure()

# reset recordNumber
recordNumber = 0
# reset the file reading (since we did some pre-processing)
F.seek(0)

# 1024 is valid for current version of Windows but should really get this value from somewhere         
record = F.read(1024)


while record != "":
    
     MFTR = decodeMFTHeader(record);
    
     if options.debug:    print '-->Record number: %d\n\tMagic: %s Attribute offset: %d Flags: %s Size:%d' %  (recordNumber, MFTR['magic'], MFTR['attr_off'], hex(int(MFTR['flags'])), MFTR['size'])
     
     if MFTR['magic'] == 0x44414142:
        if options.debug: print "BAAD MFT Record"
        MFTR['baad'] = True
     
     else:
          
          ReadPtr = MFTR['attr_off']
              
          while (ReadPtr < 1024):
          
              ATRrecord = decodeATRHeader(record[ReadPtr:])
              if ATRrecord['type'] == 0xffffffff:             # End of attributes
                  break
          
              if options.debug:        print "Attribute type: %x Length: %d Res: %x" % (ATRrecord['type'], ATRrecord['len'], ATRrecord['res'])
      
              if ATRrecord['type'] == 0x10:                   # Standard Information
                  if options.debug: print "Stardard Information:\n++Type: %s Length: %d Resident: %s Name Len:%d Name Offset: %d" % (hex(int(ATRrecord['type'])),ATRrecord['len'],ATRrecord['res'],ATRrecord['nlen'],ATRrecord['name_off'])
                  SIrecord = decodeSIAttribute(record[ReadPtr+ATRrecord['soff']:])
                  MFTR['si'] = SIrecord
                  if options.debug: print "++CRTime: %s\n++MTime: %s\n++ATime: %s\n++EntryTime: %s" % (SIrecord['crtime'].dtstr, SIrecord['mtime'].dtstr, SIrecord['atime'].dtstr, SIrecord['ctime'].dtstr)
              
              elif ATRrecord['type'] == 0x20:                 # Attribute list
                  if options.debug: print "Attribute list"
                  if ATRrecord['res'] == 0:
                      ALrecord = decodeAttributeList(record[ReadPtr+ATRrecord['soff']:])
                      MFTR['al'] = ALrecord
                      if options.debug: print "Name: %s"  % (ALrecord['name'])
                  else:
                      if options.debug: print "Non-resident Attribute List?"
                      MFTR['al'] = None
                      
              elif ATRrecord['type'] == 0x30:                 # File name
                  if options.debug: print "File name record"
                  FNrecord = decodeFNAttribute(record[ReadPtr+ATRrecord['soff']:])
                  MFTR['fn',MFTR['fncnt']] = FNrecord
                  MFTR['fncnt'] = MFTR['fncnt'] + 1
                  if options.debug: print "Name: %s (%d)" % (FNrecord['name'],MFTR['fncnt'])
                  if FNrecord['crtime'] != 0:
                      if options.debug: print "\tCRTime: %s MTime: %s ATime: %s EntryTime: %s" % (FNrecord['crtime'].dtstr, FNrecord['mtime'].dtstr, FNrecord['atime'].dtstr, FNrecord['ctime'].dtstr)
      
              elif ATRrecord['type'] == 0x40:                 #  Object ID
                  ObjectIDRecord = decodeObjectID(record[ReadPtr+ATRrecord['soff']:])
                  MFTR['objid'] = ObjectIDRecord
                  if options.debug: print "Object ID"
                  
              elif ATRrecord['type'] == 0x50:                 # Security descriptor
                  MFTR['sd'] = True
                  if options.debug: print "Security descriptor"
      
              elif ATRrecord['type'] == 0x60:                 # Volume name
                  MFTR['volname'] = True
                  if options.debug: print "Volume name"
                  
              elif ATRrecord['type'] == 0x70:                 # Volume information
                  if options.debug: print "Volume info attribute"
                  VolumeInfoRecord = decodeVolumeInfo(record[ReadPtr+ATRrecord['soff']:])
                  MFTR['volinfo'] = VolumeInfoRecord
                  
              elif ATRrecord['type'] == 0x80:                 # Data
                  MFTR['data'] = True
                  if options.debug: print "Data attribute"
      
              elif ATRrecord['type'] == 0x90:                 # Index root
                  MFTR['indexroot'] = True
                  if options.debug: print "Index root"
      
              elif ATRrecord['type'] == 0xA0:                 # Index allocation
                  MFTR['indexallocation'] = True
                  if options.debug: print "Index allocation"
                  
              elif ATRrecord['type'] == 0xB0:                 # Bitmap
                  MFTR['bitmap'] = True
                  if options.debug: print "Bitmap"
      
              elif ATRrecord['type'] == 0xC0:                 # Reparse point
                  MFTR['reparsepoint'] = True
                  if options.debug: print "Reparse point"
      
              elif ATRrecord['type'] == 0xD0:                 # EA Information
                  MFTR['eainfo'] = True
                  if options.debug: print "EA Information"
       
              elif ATRrecord['type'] == 0xE0:                 # EA
                  MFTR['ea'] = True
                  if options.debug: print "EA"
      
              elif ATRrecord['type'] == 0xF0:                 # Property set
                  MFTR['propertyset'] = True
                  if options.debug: print "Property set"
      
              elif ATRrecord['type'] == 0x100:                 # Logged utility stream
                  MFTR['loggedutility'] = True
                  if options.debug: print "Logged utility stream"
                  
              else:
                  if options.debug: print "Found an unknown attribute"
                  
              if ATRrecord['len'] > 0:
                  ReadPtr = ReadPtr + ATRrecord['len']
              else:
                  if options.debug: print "ATRrecord->len < 0, exiting loop"
                  break

          if ( MFTR['fncnt'] > 0 ):
              MFTR['filename'] = ''
              buildingBlockFolder = getFolderPath( MFTR['fn',MFTR['fncnt']-1]['par_ref'] )
              MFTR['filename'] = MFTR['filename'] + '/' + MFTR['fn',MFTR['fncnt']-1]['name']
              MFTR['filename'] = MFTR['filename'].replace('//','/')
              if options.debug: print "Filename (with path): %s" % MFTR['filename']
		
              
     record = F.read(1024)
    
     if options.anomaly and 'baad' not in MFTR:
          anomalyDetect()
          
     writeCSVFile()
     recordNumber = recordNumber + 1
    
#    if recordNumber > 100:
#        sys.exit()
   
F.close()
         
         
