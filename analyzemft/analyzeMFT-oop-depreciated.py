#!/usr/bin/env python

__description__ = 'analyzeMFT.py - a module for reading the NTFS $MFT file and analyzing/working with its contents'
__author__ = 'David Kovar, Matt Sabourin'
__version__ = '2.0'
__date__ = '2011-07-01'

# Author: David Kovar [dkovar <at> gmail [dot] com]
# Author: Matt Sabourin [mdsabourin <at> gmail [dot] com]
# Name: analyzeMFT.py
#
# Copyright (c) 2010 David Kovar. All rights reserved.
# This software is distributed under the Common Public License 1.0
#



'''
Documentation

Usage: analyzeMFT.py [options]

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -f FILENAME, --filename=FILENAME
                         [Required] Name of the MFT file to process.
  -d, --debug            [Optional] Turn on debugging output.
  -p, --fullpath         [Optional] Print full paths in output (see comments on code).
  -n, --fntimes          [Optional] Use MAC times from FN attribute instead of
                        SI attribute.
  -a, --anomaly          [Optional] Turn on anomaly detection.
  -b BODYFILE, --bodyfile=BODYFILE
                         [Optional] Write MAC information in mactimes format
                        to this file.
  -m MOUNTPOINT, --mountpoint=MOUNTPOINT
                         [Optional] The mountpoint of the filesystem that held
                        this MFT.
  -g, --gui              [Optional] Use GUI for file selection.
  -o OUTPUT, --output=OUTPUT
                         [Optional] Write analyzeMFT results to this file.


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
                    

Version 2.0: Matt Sabourin - Created an object-oriented version of analyzeMFT.py.  Most of the MFT analysis code
             and other logic was retained from the original version (along with the comments).
             The OO version is structured for importing the module directly into the python 
             interpreter to allow for manual interaction with the MFT.  The module can also be 
             imported into other python scripts that need to work with an MFT.
             
             In addition to switching to OO, I added following code:
             - Allow printing of full path file names
             - Allow use of time values from FN attribute instead of SI
             - Fixed issue with bodyfile output and newest version of mactimes - use longs vs floats for times
             - Bodyfile now includes MFT (physical) record number
             - Bodyfile now includes zero for MD5 value
						 - anomalyDetect also flags SI attribues with zero microsecond

             Fixed (?) potential issues with analyzeMFT output
             - If a record w/o an SI attribute follows a record that has an SI attribute, the second record
               was printing times for the previous record's SI attribute
             - Printing out name, times for FN[0] (first FN) attribute

---------------------------

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

# Changelog (2.0)
# 2011-04-07 MS - Changed range(0,len(self.mft)-1) to range(0,len(self.mft))
#		  We were missing the last item in the list
#
# 2011-06-26 MS - Added yes/no dialog when user requests GUI.  The dialog is used to determine if
#                 the user also wants a bodyfile produced.
#
# 2011-07-17 MS - Added MFTEntry method to return long name
#                 Updated various MFTEntry methods to use the MFTEntry.longName() method instead of
#                   selecting a specific FN entry
#                 Fixed bug where we weren't printing info for $MFT (thx David)
#                 Fixed bug with MFTEntry.anomalyDetect - incorrect reference to SI attribute and needed None check
#                 Added code to force MFTEntry to call self.anomalyDetect in initialize method so the corresponding
#                   attributes get set.  This is needed if user is producing analyzeMFT style output but did not call
#                   for anomaly detection (which prints to STDOUT).  Without this call in initialize method, we were
#                   producing incorrect values for the analyzeMFT output
#
# 2011-07-18 MS - Switched out several calls of form if foo in dict.keys() to a try/except block.  This GREATLY
#                   improved performance of the overall program.  cProfile times dropped from 228 secs to 59 secs for
#                   test MFT file
# 2011-07-20 MS - Fixed bug in fullPath() method where MFTEntry that had a parent without FN attributes would
#                   cause an error.  If we hit this case, insert ???? into the path and break out of loop



# Todo  (2.0)
# - Improve comments / documentation
# - Update MFT.getEntryMactimeFormat and MFTEntry with code that determines file size.
#	  MFTEntry should have an attribute with this value and maybe an exposed method to determine it.
# - Find the best way to determine which FN entry has the long name of the file (maybe just loop)
# - Need to improve processing performance; processing a large MFT takes too long.
# X Find way to determine the appropriate values for UID/GID in mactime format, if possible
# - Update MFT.findAnomaly to only call fullPath if that was specified on command line.
# - Wrap the GUI library imports in try/catch block
# - Research the proper value for inode in a bodyfile if the entry is for a deleted file/folder
# - Research how mode_as_string is determined and displayed for NTFS (can we just display file/folder?)
# - The MFTEntry object should have methods to write a row for either bodyfile or output file. 
#   Right now these live at MFT level to deal with fullpath, not proper OO / logical location for this
#   Requires creating a way for MFTEntry to hold its own fullpath, which in turn requires ability to 
#   notify child MFTEntries if the name changes. (Do MFTEntries know about children?) Pseudo code follows
#   def updatepath:
#			self.fullpath = newpathvalue
#     If self.haschildren:
#       for child in self.children:
#         child.updatepath  
#   Temp "fix" implemented, need a better long-term strategy
#	- Need better handling of full path and analyzeMFT style output.  Right now, FN[0] will have shortened
#   file name, but long names in parent directories.  The fullPath function can provide shortened names 
#   for each part of the full path, but we need a way to call it for each FN[i] attribute
#


import struct, sys, ctypes, re, time, unicodedata, csv, binascii, os, platform
from datetime import date, datetime
from optparse import OptionParser
# import fnmatch


# Globals

SIAttributeSizeXP = 72
SIAttributeSizeNT = 48


class MFT:
	'''Object to represent the $MFT file as a whole.  Contains methods that work across the MFT.
	Also has members that provide quick access to specific/special MFT Entries.
	'''

	def __init__(self,filename=None,mountpoint='?',anomaly=False,debug=False):
		self.filename = filename
		self.mountpoint = mountpoint
		self.anomaly = anomaly
		self.mft = {}
		self.debug = debug

		# MS - Bring attributes of specific MFT entries to top level for easier viewing
		self.volinfo = None
		self.volname = ''


		if self.filename and self.filename != '':
			self.loadFromFile(self.filename)


	def loadFromFile(self,filename):
		''' Method that reads a $MFT and builds a dictionary containing MFTEntry objects.
		The MFT record number is used as the key to the dictionary.
		Currently, the MFT record number represents the physical position in the MFT - this may be incorrect
		'''

		try:
			mftFile = open(filename,'rb')
		except:
			print "[!]  Unable to open file: %s" % filename
			sys.exit()

		print "[+]  Reading MFT file..."

		recordNumber = 0
		record = mftFile.read(1024)

		while record != "":
			tmpMFTEntry = MFTEntry(record,recordNumber,self.debug)
			self.mft[recordNumber] = tmpMFTEntry

			# MS - Bring attributes of specific MFT entries to top level for easier viewing
			#if tmpMFTEntry.volname:
			#	self.volname = tmpMFTEntry.volname
	
			#if tmpMFTEntry.volinfo:
			#	self.volinfo = tmpMFTEntry.volinfo

			record = mftFile.read(1024)
			recordNumber = recordNumber + 1

#		if self.anomaly and not tmpMFTEntry.baad:
#			tmpMFTEntry.anomalyDetect()
#
#			writeCSVFile()

		mftFile.close()

	def fullPath(self,rec_num,justPath=False,fnNum=-1):
		''' Method will return a string containing the full path of the specified MFT entry.
		If a mountpoint was not set on the MFT object, it defaults to a question mark.
		Input is an MFT record number.
		'''

		# MS - Using last FN entry because it has long name. Need to find better way to 
		#      find this type of FN entry
		# MS - Switch to use last FN entry by default, but allow caller to change value
		# MS - Allow caller to just request the path w/o the actual filename
		fp = []

		try:
			entry = self.mft[rec_num]
		except KeyError:
			return ''

		#print "fnNum %d" % fnNum

		if len(entry.FN):
			while entry.rec_num != entry.FN[fnNum].par_ref:
				fp.append(entry.FN[fnNum].name)
				entry = self.mft[entry.FN[fnNum].par_ref]
				# MS - Handle case where an entry in the full path lacks FN attributes
				#        We set the name for this entry to ???? to raise awareness of 
				#        this entry
				if not len(entry.FN):
					fp.append('????')
					break
				
			fp.append(self.mountpoint)
			
			# MS - Handle special case for root folder, insert emptry string so the 
			#      join operation results in driveletter:\
			if len(fp) == 1:
				fp.insert(0,'')

			# MS - If we just need the path, delete file name item from list
			if justPath:
				del(fp[0])

			# MS - Path entries were pushed onto list in reverse order, so we need to
			#      reverse the list while joining with the OS separator
			return '\\'.join(fp[::-1])
		else:
			return '?'


	def anomalyDetect(self):
		''' Loop through the MFTEntry objects within the MFT and print a message for each entry where:
			- SI attribute create time before FN attribute create time
			- FN attribute create time of 0
			- FN attribute create time with microsecond of 0
			- SI attribute create time with microsecond of 0
		'''

		for entry in self.mft.keys():
			if not self.mft[entry].baad:
				self.mft[entry].anomalyDetect()
				if self.mft[entry].si_fn_shift:
					print "Anomaly - SI-FN Time Shift: [%d] %s" % (entry,self.fullPath(entry))

				if self.mft[entry].usec_zero:
					print "Anomaly - Microseconds at zero: [%d] %s" % (entry,self.fullPath(entry))
	

	def getEntryMactimeFormat(self,rec_num,useFullPath=True,useFNtimes=False):
		mactime = ''
		fullpath = ''

		try:
			entry = self.mft[rec_num]

		except KeyError:
			return mactime


		if useFullPath:
			fullpath = self.fullPath(rec_num)

		mactime = entry.getMactimeFormat(fullpath,useFNtimes)

		return mactime



	def printBodyFile(self,useFullPath=True,useFNtimes=False):
		''' Print a "bodyfile" in mactimes format.  See the Sleuth Kit web site 
			<http://sleuthkit.org> for more information about the format (and mactimes)
			Provide options for printing of fullpaths and using times from FN attribute.
		'''
		print "[+]  Printing body file [FullPath=%s, FNtimes=%s]..." % (str(useFullPath),str(useFNtimes))

		#for count in range(0,len(self.mft)-1):
		for count in range(0,len(self.mft)):
			mactimeEntry = self.getEntryMactimeFormat(count,useFullPath,useFNtimes)
			if mactimeEntry:
				print mactimeEntry



	def writeBodyFile(self,filename,useFullPath=True,useFNtimes=False):
		''' Write a "bodyfile" in mactimes format.  See the Sleuth Kit web site 
			<http://sleuthkit.org> for more information about the format (and mactimes)
			Provide options for printing of fullpaths and using times from FN attribute.
		'''

		bfile = open(filename,'w')

		print "[+]  Writing body file [FullPath=%s, FNtimes=%s]..." % (str(useFullPath),str(useFNtimes))

		count = 0

		#while count < len(self.mft):
		for count in range(0,len(self.mft)):
			mactimeEntry = self.getEntryMactimeFormat(count,useFullPath,useFNtimes)
			if mactimeEntry:
				bfile.write(mactimeEntry + '\n')

		#	count = count + 1


	def getEntryCSVFormat(self,rec_num,useFullPath=True,useFNtimes=False):
		csvEntry = []
		fullpath = ''

		try:
			entry = self.mft[rec_num]

		except KeyError:
			return csvEntry


		if useFullPath:
			fullpath = self.fullPath(rec_num,justPath=True)
	
		csvEntry = entry.getCSVFormat(fullpath,useFNtimes)

		return csvEntry



	def writeOutputFile(self,filename,useFullPath=True,useFNtimes=False):
		''' Write an analyzeMFT style output file (a CSV).
			Provide options for printing of fullpaths and using times from FN attribute.
		'''

		ofile = csv.writer(open(filename,'w'),dialect=csv.excel,quoting=1)

		print "[+]  Writing analyzeMFT output file [FullPath=%s, FNtimes=%s]..." % (str(useFullPath),str(useFNtimes))

		# Write headers
		ofile.writerow(['Record Number', 'Good', 'Active', 'Record type',
#			'$Logfile Seq. Num.',
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
 
		count = 0

		#while count < len(self.mft):
		for count in range(0,len(self.mft)):
			csvEntry = self.getEntryCSVFormat(count,useFullPath,useFNtimes)
			if len(csvEntry):
				ofile.writerow(csvEntry)





class MFTEntry:
	''' Object that represents an entry in the MFT.  Most of the MFT decoding logic is located here.
	'''

	def __init__(self,record=None,recordNumber=None,debug=False):
		self.debug = debug		

		self.rec_num = recordNumber
		self.magic = struct.unpack("<I", record[:4])[0]
		self.upd_off = struct.unpack("<H",record[4:6])[0]
		self.upd_cnt = struct.unpack("<H",record[6:8])[0]
		self.lsn = struct.unpack("<d",record[8:16])[0]
		self.seq = struct.unpack("<H",record[16:18])[0]
		self.link = struct.unpack("<H",record[18:20])[0]
		self.attr_off = struct.unpack("<H",record[20:22])[0]
		self.flags = struct.unpack("<H", record[22:24])[0]
		self.size = struct.unpack("<I",record[24:28])[0]
		self.alloc_sizef = struct.unpack("<I",record[28:32])[0]
		self.base_ref = struct.unpack("<Lxx",record[32:38])[0]
		self.base_seq = struct.unpack("<H",record[38:40])[0]
		self.next_attrid = struct.unpack("<H",record[40:42])[0]
		self.f1 = record[42:44]
		self.entry = record[44:48]
		self.fncnt = 0                              # Counter for number of FN attributes

		self.baad = False
		
		self.ATR = None
		self.AL = None
		self.SI = None
		self.FN = []
		self.objid = None

		self.sd = False
		self.volname = False
		self.volinfo = None
		self.data = False
		self.indexroot = False
		self.indexallocation = False
		self.bitmap = False
		self.reparsepoint = False
		self.eainfo = False
		self.ea = False
		self.propertyset = False
		self.loggedutility = False
		self.si_fn_shift = False
		self.usec_zero = False

		self.notes = ''

		if record is not None and recordNumber is not None:
			self.loadFromRecord(record,recordNumber,debug)

			# MS - Need to call the anomalyDetect function to set the appropriate members, in case
			#      the use did not ask for anomaly detection, but is producing output in analyzeMFT format
			self.anomalyDetect()


	def loadFromRecord(self,record,recordNumber,debug=False):
		if self.debug:    
			print '-->Record number: %d\n\tMagic: %s\n\tAttribute offset: %d\n\tFlags: %s\n\tSize:%d' %  \
				(recordNumber, self.magic, self.attr_off, hex(int(self.flags)), self.size)

		if self.magic == 0x44414142:
			if self.debug: 
				print "BAAD MFT Record"
				self.baad = True
		else:
			ReadPtr = self.attr_off

			while (ReadPtr < 1024):
				self.ATR = ATRrecord(record[ReadPtr:])
				if self.ATR.type == 0xffffffff:             # End of attributes
					break

				if self.debug:
					print "Attribute type: %x Length: %d Res: %x" % (self.ATR.type, self.ATR.len, self.ATR.res)

				if self.ATR.type == 0x10:                   # Standard Information
					if self.debug: 
						print "Stardard Information:\n++Type: %s Length: %d Resident: %s Name Len:%d Name Offset: %d" % \
							(hex(int(self.ATR.type)),self.ATR.len,self.ATR.res,self.ATR.nlen,self.ATR.name_off)
					self.SI = SIAttribute(record[ReadPtr+self.ATR.soff:])
					if self.debug:
						print "++CRTime: %s\n++MTime: %s\n++ATime: %s\n++EntryTime: %s" % (self.SI.crtime.dtstr, self.SI.mtime.dtstr, self.SI.atime.dtstr, self.SI.ctime.dtstr)

				elif self.ATR.type == 0x20:                 # Attribute list
					if self.debug: print "Attribute list"
					if self.ATR.res == 0:
						self.AL = AttributeList(record[ReadPtr+self.ATR.soff:])
						if self.AL.hexFlag:
							self.addNote('Filename - chars converted to hex')
						if self.debug: print "Name: %s"  % (self.AL.name)
					else:
						if self.debug: print "Non-resident Attribute List?"

				elif self.ATR.type == 0x30:                 # File name
					if self.debug: print "File name record"
					self.FN.append(FNAttribute(record[ReadPtr+self.ATR.soff:]))
					if self.FN[-1].hexFlag:
						self.addNote('Filename - chars converted to hex')

					if self.debug: print "Name: %s" % (self.FN[-1].name)
					if self.FN[-1].crtime != 0:
						if self.debug: 
							print "\tCRTime: %s\n\tMTime: %s\n\tATime: %s\n\tEntryTime: %s" % (self.FN[-1].crtime.dtstr, self.FN[-1].mtime.dtstr, self.FN[-1].atime.dtstr, self.FN[-1].ctime.dtstr)

				elif self.ATR.type == 0x40:                 #  Object ID
					self.objid = ObjectID(record[ReadPtr+self.ATR.soff:])
					if self.debug: print "Object ID"

				elif self.ATR.type == 0x50:                 # Security descriptor
					self.sd = True
					if self.debug: print "Security descriptor"

				elif self.ATR.type == 0x60:                 # Volume name
					self.volname = True
					if self.debug: print "Volume name"

				elif self.ATR.type == 0x70:                 # Volume information
					if self.debug: print "Volume info attribute"
					self.volinfo = VolumeInfo(record[ReadPtr+self.ATR.soff:],self.debug)

				elif self.ATR.type == 0x80:                 # Data
					self.data = True
					if self.debug: print "Data attribute"

				elif self.ATR.type == 0x90:                 # Index root
					self.indexroot = True
					if self.debug: print "Index root"

				elif self.ATR.type == 0xA0:                 # Index allocation
					self.indexallocation = True
					if self.debug: print "Index allocation"

				elif self.ATR.type == 0xB0:                 # Bitmap
					self.bitmap = True
					if self.debug: print "Bitmap"

				elif self.ATR.type == 0xC0:                 # Reparse point
					self.reparsepoint = True
					if self.debug: print "Reparse point"

				elif self.ATR.type == 0xD0:                 # EA Information
					self.eainfo = True
					if self.debug: print "EA Information"

				elif self.ATR.type == 0xE0:                 # EA
					self.ea = True
					if self.debug: print "EA"

				elif self.ATR.type == 0xF0:                 # Property set
					self.propertyset = True
					if self.debug: print "Property set"

				elif self.ATR.type == 0x100:                 # Logged utility stream
					self.loggedutility = True
					if self.debug: print "Logged utility stream"

				else:
					if self.debug: print "Found an unknown attribute"

				if self.ATR.len > 0:
					ReadPtr = ReadPtr + self.ATR.len
				else:
					if self.debug: print "ATRrecord->len < 0, exiting loop"
					break

	def decodeMagic(self):
		if self.magic == 0x454c4946:
			return "Good"
		elif self.magic == 0x44414142:
			return 'Bad'
		elif self.magic == 0x00000000:
			return 'Zero'
		else:
			return 'Unknown'

	# decodeMFTisactive and decodeMFTrecordtype both look at the flags field in the MFT header.
	# The first bit indicates if the record is active or inactive. The second bit indicates if it
	# is a file or a folder.
	#
	# I had this coded incorrectly initially. Spencer Lynch identified and fixed the code. Many thanks!

	# MS - change decodeMFTisactive into boolean function
	def isActive(self):
		if self.flags & 0x0001:
			#return 'Active'
			return True
		else:
			#return 'Inactive'
			return False

	def recordType(self):
		tmpBuffer = self.flags
		if self.flags & 0x0002:
			tmpBuffer = 'Folder'
		else:
			tmpBuffer = 'File'
		if self.flags & 0x0004:
			tmpBuffer = "%s %s" % (tmpBuffer, '+ Unknown1')
		if self.flags & 0x0008:
			tmpBuffer = "%s %s" % (tmpBuffer, '+ Unknown2')
		
		return tmpBuffer

	def addNote(self,s):
		if len(self.notes):
			self.notes = "%s | %s |" % (self.notes, s)
		else:
			self.notes = "%s" % s


	def anomalyDetect(self):
		''' Check the entry for the following anomalous conditions:
			- SI attribute create time before FN attribute create time
			- FN attribute create time of 0
			- FN attribute create time with microsecond of 0
			- SI attribute create time with microsecond of 0
			The method does not return a value, instead it sets the appropriate
			attribute to true (either si_fn_shift or usec_zero)
		'''
		# Check for STD create times that are before the FN create times
		if len(self.FN) > 0:
			# MS - Adjusted to check every FN entry, not just the first
			for fn in self.FN:
				try:
					if (fn.crtime.dt == 0) or (self.SI.crtime.dt < fn.crtime.dt):
						self.si_fn_shift = True
					# This is a kludge - there seem to be some legit files that trigger an exception 
					# in the above. Needs to be investigated
				except:
					self.si_fn_shift = True

				# MS - this checks the create time of the FN entry, SI check is later
				# Check for STD create times with a nanosecond value of '0'
				if fn.crtime.dt != 0:
					if fn.crtime.dt.microsecond == 0:
						self.usec_zero = True


		# MS - check for SI attribute with create time that has a zero microsecond
		if self.SI is not None and self.SI.crtime.dt != 0:
			if self.SI.crtime.dt.microsecond == 0:
				self.usec_zero = True


	def longName(self):
		''' Function that will return the long name for the MFT entry, based on
			values found in FN entries.  Don't know if the long name is always in a
			specific position in the FN entry list, so we just loop through the list
			and return the longest value.  This should be sufficient, as it's unusual to
			have a large number of FN entries.
		'''

		# MS - Loop through the FN entries and return the longest name string
		lname = ''
		for fn in self.FN:
			#print 'debug: FN name %s len1 %d len2 %d' % (fn.name,len(fn.name),len(lname))
			if len(fn.name) > len(lname):
				lname = fn.name

		return lname


	def getMactimeFormat(self,fullPath='',useFNtimes=False):
		# MD5|name|inode|mode_as_string|UID|GID|size|atime|mtime|ctime|crtime
		# To do - figure out file size

		mactime = ''
		name = ''

		if len(self.FN) > 0:
			if fullPath:
				name = fullPath
			else:
				# MS - change to print the long name.  Might need to add code to ensure the FN attr with
				# the longest name is also the FN attr we are pulling times for
				#name = self.FN[-1].name
				name = self.longName()
		else:
			name = 'No FN Attribute'
			
		if not self.isActive():
			name = name + ' (deleted)'

		# MD5|name|inode|mode_as_string|UID|GID|size|atime|mtime|ctime|crtime
		# MS - [FIXME] mactimes wants values for inode, GID, UID, so provide dummy values for now
		# MS - Currently setting inode to record number from the MFT... This may not be the 
		#      proper method for deleted files?
		#mactime = '%s|%s|%s|%s|%s|%s|%s' % ('',name,'0','','0','0','')
		mactime = '%s|%s|%s|%s|%s|%s|%s' % ('0',name,str(self.rec_num),'','0','0','')
		# Give caller option to determine which set of times are used for the mactime entry
			
		if useFNtimes:
			if len(self.FN):
				fn = self.FN[-1]
				# MS - the WindowsTime class returns a unixtime that is a float
				#      mactimes expects times to be integers and won't use times that aren't
				mactime = mactime + '|%s|%s|%s|%s' % (long(fn.atime.unixtime), 
                            long(fn.mtime.unixtime),
                            long(fn.ctime.unixtime),
                            long(fn.crtime.unixtime))
			else:
				mactime = mactime + '|0|0|0|0'
		elif self.SI:
			mactime = mactime + '|%s|%s|%s|%s' % (long(self.SI.atime.unixtime),
                                            long(self.SI.mtime.unixtime),
                                            long(self.SI.ctime.unixtime),
                                            long(self.SI.crtime.unixtime))
		else:
			mactime = mactime + '|0|0|0|0'

		return mactime



	def getCSVFormat(self,path='',useFNtimes=False):
		csvEntry = []

		csvEntry.extend([self.rec_num,self.decodeMagic()])
		if self.isActive():
			csvEntry.append('Active')
		else:
			csvEntry.append('Inactive')
		csvEntry.extend([self.recordType(),str(self.seq)])
		
		if len(self.FN):
			# MS - add the path value - if the user requested full path this will provide value,
			#      else we're just prepending an empty string
			#csvEntry.extend([str(self.FN[0].par_ref),str(self.FN[0].par_seq),path + '\\' + self.FN[0].name])
			csvEntry.extend([str(self.FN[0].par_ref),str(self.FN[0].par_seq),path + '\\' + self.longName()])

			# MS - If user wanted fullpath, use that else use name of first FN attribute to match old behavior
			#if fullPath:
			#	csvEntry.append(fullPath)
			#else:
			#	csvEntry.append(self.FN[0].name)

			csvEntry.extend([self.SI.crtime.dtstr,self.SI.mtime.dtstr,self.SI.atime.dtstr,self.SI.ctime.dtstr])
			csvEntry.extend([self.FN[0].crtime.dtstr,self.FN[0].mtime.dtstr,self.FN[0].atime.dtstr,self.FN[0].ctime.dtstr])
		else:
			csvEntry.extend(['NoParent','NoParent','NoFNRecord'])

			if self.SI:
				csvEntry.extend([self.SI.crtime.dtstr,self.SI.mtime.dtstr,self.SI.atime.dtstr,self.SI.ctime.dtstr])
			else:
				csvEntry.extend(['NoSIRecord','NoSIRecord','NoSIRecord','NoSIRecord'])

			csvEntry.extend(['NoFNRecord','NoFNRecord','NoFNRecord','NoFNRecord'])

		if self.objid:
			csvEntry.extend([self.objid.objid,self.objid.orig_volid,self.objid.orig_objid,self.objid.orig_domid])
		else:
			csvEntry.extend(['','','',''])

		# If this goes above four FN attributes, the number of columns will exceed the headers        
		# MS - Prepend the path value again
		for i in range(1, len(self.FN)):
			csvEntry.extend([path + '\\' + self.FN[i].name, self.FN[i].crtime.dtstr,self.FN[i].mtime.dtstr,
                       self.FN[i].atime.dtstr,self.FN[i].ctime.dtstr])

		# Pad out the remaining FN columns
		if len(self.FN) < 2:
			tmpBuffer = ['','','','','','','','','','','','','','','']
		elif len(self.FN) == 2:
			tmpBuffer = ['','','','','','','','','','']
		elif len(self.FN) == 3:
			tmpBuffer = ['','','','','']
            
		csvEntry.extend(tmpBuffer)

		csvEntry.append(self.SI is not None)
		csvEntry.append(self.AL is not None)
		csvEntry.append(len(self.FN) > 0)
		csvEntry.append(self.objid is not None)
		csvEntry.append(self.volname)
		csvEntry.append(self.volinfo is not None)

		csvEntry.extend([self.data,self.indexroot,self.indexallocation,self.bitmap,
                     self.reparsepoint,self.eainfo,self.ea,self.propertyset,
                     self.loggedutility])
		if self.notes:
			csvEntry.append(self.notes)
		else:
			csvEntry.append('None')

		
		if self.si_fn_shift:
			csvEntry.append('Y')
		else:
			csvEntry.append('N')

		if self.usec_zero:
			csvEntry.append('Y')
		else:
			csvEntry.append('N')

		return csvEntry

		
		



class ATRrecord:

	def __init__(self,record=None):
		self.len = ''
		self.res = ''
		self.nlen = ''
		self.name_off = ''
		self.flags = ''
		self.id = ''
		self.ssize = ''
		self.soff = ''
		self.idxflag  = ''
		self.start_vcn  = ''
		self.last_vcn  = ''
		self.run_off  = ''
		self.compusize  = ''
		self.f1  = ''
		self.alen  = ''
		self.ssize  = ''
		self.initsize  = ''


		if record:
			self.loadFromRecord(record)

	def loadFromRecord(self,record):
		self.type = struct.unpack("<L",record[:4])[0]
		if self.type == 0xffffffff:
			return

		self.len = struct.unpack("<L",record[4:8])[0]
		self.res = struct.unpack("B",record[8])[0]
		self.nlen = struct.unpack("B",record[9])[0]                  # This name is the name of the ADS, I think.
		self.name_off = struct.unpack("<H",record[10:12])[0]
		self.flags = struct.unpack("<H",record[12:14])[0]
		self.id = struct.unpack("<H",record[14:16])[0]
		if self.res == 0:
			self.ssize = struct.unpack("<L",record[16:20])[0]
			self.soff = struct.unpack("<H",record[20:22])[0]
			self.idxflag = struct.unpack("<H",record[22:24])[0]
		else:
			self.start_vcn = struct.unpack("<d",record[16:24])[0]
			self.last_vcn = struct.unpack("<d",record[24:32])[0]
			self.run_off = struct.unpack("<H",record[32:34])[0]
			self.compusize = struct.unpack("<H",record[34:36])[0]
			self.f1 = struct.unpack("<I",record[36:40])[0]
			self.alen = struct.unpack("<d",record[40:48])[0]
			self.ssize = struct.unpack("<d",record[48:56])[0]
			self.initsize = struct.unpack("<d",record[56:64])[0]



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
        return (t*1e-7 - 11644473600)


class FNAttribute:

	def __init__(self,record=None,unicodeHack=True):
		self.par_ref = ''
		self.par_seq = ''
		self.crtime = None
		self.mtime = None
		self.ctime = None
		self.atime = None
		self.alloc_fsize = ''
		self.real_fsize = ''
		self.flags = ''
		self.nlen = ''
		self.nspace = ''
		self.hexFlag = False
		self.unicodeHack = unicodeHack

		if record:
			self.loadFromRecord(record)


	def loadFromRecord(self,record):
	
		# File name attributes can have null dates.
		
		self.par_ref = struct.unpack("<Lxx", record[:6])[0]      # Parent reference nummber
		self.par_seq = struct.unpack("<H",record[6:8])[0]        # Parent sequence number
		self.crtime = WindowsTime(struct.unpack("<L",record[8:12])[0],struct.unpack("<L",record[12:16])[0])
		self.mtime = WindowsTime(struct.unpack("<L",record[16:20])[0],struct.unpack("<L",record[20:24])[0])
		self.ctime = WindowsTime(struct.unpack("<L",record[24:28])[0],struct.unpack("<L",record[28:32])[0])
		self.atime = WindowsTime(struct.unpack("<L",record[32:36])[0],struct.unpack("<L",record[36:40])[0])
		self.alloc_fsize = struct.unpack("<d",record[40:48])[0]
		self.real_fsize = struct.unpack("<d",record[48:56])[0]
		self.flags = struct.unpack("<d",record[56:64])[0]            # 0x01=NTFS, 0x02=DOS
		self.nlen = struct.unpack("B",record[64])[0]
		self.nspace = struct.unpack("B",record[65])[0]

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
		
		if (self.unicodeHack):
			self.name = ''
			for i in range(66, 66 + self.nlen*2):
				if record[i] != '\x00':                         # Just skip over nulls
					if record[i] > '\x1F' and record[i] < '\x80':          # If it is printable, add it to the string
						self.name = self.name + record[i]
					else:
						self.name = "%s0x%02s" % (self.name, record[i].encode("hex"))
						self.hexFlag = True

		# This statement produces a valid unicode string, I just cannot get it to print correctly
		# so I'm temporarily hacking it with the if (self.unicodeHack) above.
		else:
			self.name = record[66:66+self.nlen*2]
			# This didn't work
			#    self.name = struct.pack("\u    
			#    for i in range(0, self.nlen*2, 2):
			#        self.name=self.name + struct.unpack("<H",record[66+i:66+i+1])
			#
			# What follows is ugly. I'm trying to deal with the filename in Unicode and not doing well.
			# This solution works, though it is printing nulls between the characters. It'll do for now.
			#    d['name'] = struct.unpack("<%dH" % (int(d['nlen'])*2),s[66:66+(d['nlen']*2)])
			#    d['name'] = s[66:66+(d['nlen']*2)]
			#    d['decname'] = unicodedata.normalize('NFKD', d['name']).encode('ASCII','ignore')
			#    d['decname'] = unicode(d['name'],'iso-8859-1','ignore')

			self.name = struct.unpack("<%dH" % (int(self.nlen)*2),record[66:66+(self.nlen*2)])
			self.name = record[66:66+(self.nlen*2)]
			self.decname = unicodedata.normalize('NFKD', self.name).encode('ASCII','ignore')
			self.decname = unicode(self.name,'iso-8859-1','ignore')
		


class SIAttribute:

	def __init__(self,record=None):

		self.crtime = None
		self.mtime = None
		self.ctime = None
		self.atime = None
		self.dos = ''
		self.maxver = ''
		self.ver = ''
		self.class_id = ''
		self.own_id = ''
		self.sec_id = ''
		self.quota = ''
		self.usn = ''

		if record:
			self.loadFromRecord(record)


	def loadFromRecord(self,record):
		self.crtime = WindowsTime(struct.unpack("<L",record[:4])[0],struct.unpack("<L",record[4:8])[0])
		self.mtime = WindowsTime(struct.unpack("<L",record[8:12])[0],struct.unpack("<L",record[12:16])[0])
		self.ctime = WindowsTime(struct.unpack("<L",record[16:20])[0],struct.unpack("<L",record[20:24])[0])
		self.atime = WindowsTime(struct.unpack("<L",record[24:28])[0],struct.unpack("<L",record[28:32])[0])
		self.dos = struct.unpack("<I",record[32:36])[0]          # 4
		self.maxver = struct.unpack("<I",record[36:40])[0]       # 4
		self.ver = struct.unpack("<I",record[40:44])[0]          # 4
		self.class_id = struct.unpack("<I",record[44:48])[0]     # 4
		self.own_id = struct.unpack("<I",record[48:52])[0]       # 4
		self.sec_id = struct.unpack("<I",record[52:56])[0]       # 4
		self.quota = struct.unpack("<d",record[56:64])[0]        # 8
		self.usn = struct.unpack("<d",record[64:72])[0]          # 8 - end of date to here is 40




class AttributeList:

	def __init__(self,record=None,unicodeHack=True):
		self.hexFlag = False
		self.type = ''
		self.len = ''
		self.nlen = ''
		self.f1 = ''
		self.start_vcn = ''
		self.file_ref = ''
		self.seq = ''
		self.id = ''
		self.name = ''
		self.unicodeHack = unicodeHack

		if record:
			self.loadFromRecord(record)


	def loadFromRecord(self,record):
		self.type = struct.unpack("<I",record[:4])[0]                # 4
		self.len = struct.unpack("<H",record[4:6])[0]                # 2
		self.nlen = struct.unpack("B",record[6])[0]                  # 1
		self.f1 = struct.unpack("B",record[7])[0]                    # 1
		self.start_vcn = struct.unpack("<d",record[8:16])[0]         # 8
		self.file_ref = struct.unpack("<Lxx",record[16:22])[0]       # 6
		self.seq = struct.unpack("<H",record[22:24])[0]              # 2
		self.id = struct.unpack("<H",record[24:26])[0]               # 4
		if (self.unicodeHack):
			for i in range(26, 26 + self.nlen*2):
				if record[i] != '\x00':                         # Just skip over nulls
					if record[i] > '\x1F' and record[i] < '\x80':          # If it is printable, add it to the string
						self.name = self.name + record[i]
					else:
						self.name = "%s0x%02s" % (self.name, record[i].encode("hex"))
						self.hexFlag = True
		else:
			self.name = record[26:26+self.nlen*2]


class VolumeInfo:
	def __init__(self,record=None,debug=False):
		self.f1 = ''
		self.maj_ver = ''
		self.min_ver = ''
		self.flags = ''
		self.f2 = ''
		self.debug = debug

	def loadFromRecord(self,record):
		self.f1 = struct.unpack("<d",record[:8])[0]                  # 8
		self.maj_ver = struct.unpack("B",record[8])[0]               # 1
		self.min_ver = struct.unpack("B",record[9])[0]               # 1
		self.flags = struct.unpack("<H",record[10:12])[0]            # 2
		self.f2 = struct.unpack("<I",record[12:16])[0]               # 4

		if (self.debug):
			print "+Volume Info"
			print "++F1%d" % self.f1
			print "++Major Version: %d" % self.maj_ver
			print "++Minor Version: %d" % self.min_ver
			print "++Flags: %d" % self.flags
			print "++F2: %d" % self.f2



class ObjectID:

	def __init__(self, record=None):
		self.objid = 'Undefined'
		self.orig_volid = 'Undefined'
		self.orig_objid = 'Undefined'
		self.orig_domid = 'Undefined'

		if record and record != 0:
			self.loadFromRecord(record)

	def loadFromRecord(self,record):
		self.objid = self.FmtObjectID(record[0:16])
		self.orig_volid = self.FmtObjectID(record[16:32])
		self.orig_objid = self.FmtObjectID(record[32:48])
		self.orig_domid = self.FmtObjectID(record[48:64])

	def FmtObjectID(self,record):
		string = "%s-%s-%s-%s-%s" % (binascii.hexlify(record[0:4]),binascii.hexlify(record[4:6]),
			binascii.hexlify(record[6:8]),binascii.hexlify(record[8:10]),binascii.hexlify(record[10:16]))

		return string


#-------

def buildOptions(copyright):
	""" Function that preps the OptionParser, which parses command line args. """

	parser = OptionParser(usage="""\

Usage: %prog [options]

""",version=copyright)

	parser.add_option('-f', '--filename',
		type='string', action='store',
		help=""" [Required] Name of the MFT file to process. """)

	parser.add_option("-d", "--debug",
		action="store_true", default=False,
		help=""" [Optional] Turn on debugging output. """)

	parser.add_option("-p", "--fullpath",
		action="store_true", default=False,
		help=""" [Optional] Print full paths in output (see comments in code). """)

	parser.add_option("-n", "--fntimes",
		action="store_true", default=False,
		help=""" [Optional] Use MAC times from FN attribute instead of SI attribute. """)

	parser.add_option("-a", "--anomaly",
		action="store_true", default=False,
		help=""" [Optional] Turn on anomaly detection.""")

	parser.add_option('-b', '--bodyfile',
		type='string', action='store',
		help=""" [Optional] Write MAC information in mactimes format to this file. """)
		
	parser.add_option('-m', '--mountpoint',
		type='string', action='store',
		help=""" [Optional] The mountpoint of the filesystem that held this MFT. """)

	parser.add_option("-g", "--gui",
		action="store_true", default=False, dest="UseGUI",
		help=""" [Optional] Use GUI for file selection.""")

	parser.add_option("-o", "--output", 
		type='string',action='store',
		help=""" [Optional] Write analyzeMFT results to this file. """)

   	return parser



def handleOptions(options,parser):
	""" Function that performs various checks of the command line options
	to verify everything needed is provided. """

	if not options.filename and not options.UseGUI:
		parser.error("-f|--filename not supplied.")

	if options.bodyfile and os.path.exists(options.bodyfile):
		parser.error("-b|--bodyfile already exists!")

	if options.output and os.path.exists(options.output):
		parser.error("-o|--output already exists!")

	if not options.UseGUI and (not options.bodyfile and not options.output):
		parser.error("Must specify either an output or bodyfile argument.")




def main():
	myname = os.path.basename(sys.argv[0])
	version = "\n%s  2.0" % (myname)
	copyright = version 

	print
	print version
	print

	parser = buildOptions(copyright)

	(options, args) = parser.parse_args(sys.argv)

	handleOptions(options,parser)

	# MS - If user wants GUI for file selction, we need to import GUI libraries.  This will 
	#      blow up with standard Python stack trace if these libraries are not installed
	if options.UseGUI:
		if platform.system() == "Windows":
			import win32gui

		# MS - Got errors that import * is only allowed at module level.  turns out things work even
		#      when this is commented out
		#from Tkinter import *
		import Tkinter as tk
		# MS - We don't appear to be using methods from tkCommonDialog
		#import tkCommonDialog
		import tkFileDialog
		# from Tkinter.dialog import Dialog
		# from Tkinter import commondialog
		# MS - Need to ask a yes/no question so import tkMessageBox
		import tkMessageBox

		root = tk.Tk()
		root.withdraw()
		options.filename = tkFileDialog.askopenfilename(title=myname +': MFT file to open',filetypes=[("all files", "*")])

		# If the user wants GUI prompts for filenames, ask to see what type of output they want
		# Provide a Save As dialog for each requested output format
		if tkMessageBox.askyesno(title=myname +': analyzeMFT File Required?',message='Would you like to produce an analyzeMFT output file?'):
			options.output = tkFileDialog.asksaveasfilename(title=myname +': Save Output File As')
    
		if tkMessageBox.askyesno(title=myname +': Bodyfile Required?',message='Would you like to produce a bodyfile?'):
			options.bodyfile = tkFileDialog.asksaveasfilename(title=myname +': Save Bodyfile As')


	#mft = MFT(filename=options.filename,mountpoint=options.mountpoint,anomaly=options.anomaly,debug=options.debug)
	if options.mountpoint:
		mft = MFT(filename=options.filename,mountpoint=options.mountpoint,anomaly=options.anomaly,debug=options.debug)
	else:
		mft = MFT(filename=options.filename,anomaly=options.anomaly,debug=options.debug)

	if options.bodyfile:
		mft.writeBodyFile(options.bodyfile,useFullPath=options.fullpath,useFNtimes=options.fntimes)

	if options.output:
		mft.writeOutputFile(options.output,useFullPath=options.fullpath,useFNtimes=options.fntimes)




#--------
# MS - When the file is run as a script, __name__ will equal __main__.  Otherwise, the 
#		file has been imported (by interpreter or another script), so take no action.
#--------

if __name__ == '__main__':
	main()




