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

def parse_record(raw_record, options):

    record = {}
    record['filename'] = ''
    record['notes'] = ''

    self.decodeMFTHeader(record, raw_record);

    record_number = record['recordnum']

    if options.debug:
        print '-->Record number: %d\n\tMagic: %s Attribute offset: %d Flags: %s Size:%d' % (record_number, record['magic'],
            record['attr_off'], hex(int(record['flags'])), record['size'])

    if record['magic'] == 0x44414142:
        if options.debug:
            print "BAAD MFT Record"
        record['baad'] = True
        return

    if record['magic'] != 0x454c4946:
        if options.debug:
            print "Corrupt MFT Record"
        record['corrupt'] = True
        return

    read_ptr = record['attr_off']

    while (read_ptr < 1024):

        ATRrecord = self.decodeATRHeader(raw_record[read_ptr:])
        if ATRrecord['type'] == 0xffffffff:             # End of attributes
            break

        if options.debug:
            print "Attribute type: %x Length: %d Res: %x" % (ATRrecord['type'], ATRrecord['len'], ATRrecord['res'])

        if ATRrecord['type'] == 0x10:                   # Standard Information
            if options.debug:
                print "Stardard Information:\n++Type: %s Length: %d Resident: %s Name Len:%d Name Offset: %d" % \
                     (hex(int(ATRrecord['type'])),ATRrecord['len'],ATRrecord['res'],ATRrecord['nlen'],ATRrecord['name_off'])
            SIrecord = self.decodeSIAttribute(raw_record[read_ptr+ATRrecord['soff']:], options.localtz)
            record['si'] = SIrecord
            if options.debug:
                print "++CRTime: %s\n++MTime: %s\n++ATime: %s\n++EntryTime: %s" % \
                   (SIrecord['crtime'].dtstr, SIrecord['mtime'].dtstr, SIrecord['atime'].dtstr, SIrecord['ctime'].dtstr)

        elif ATRrecord['type'] == 0x20:                 # Attribute list
            if options.debug:
                print "Attribute list"
            if ATRrecord['res'] == 0:
                ALrecord = self.decodeAttributeList(raw_record[read_ptr+ATRrecord['soff']:])
                record['al'] = ALrecord
                if options.debug:
                    print "Name: %s"  % (ALrecord['name'])
            else:
                if options.debug:
                    print "Non-resident Attribute List?"
                record['al'] = None

        elif ATRrecord['type'] == 0x30:                 # File name
            if options.debug: print "File name record"
            FNrecord = self.decodeFNAttribute(raw_record[read_ptr+ATRrecord['soff']:], options.localtz)
            record['fn',record['fncnt']] = FNrecord
            if options.debug: print "Name: %s (%d)" % (FNrecord['name'],record['fncnt'])
            record['fncnt'] = record['fncnt'] + 1
            if FNrecord['crtime'] != 0:
                if options.debug: print "\tCRTime: %s MTime: %s ATime: %s EntryTime: %s" % (FNrecord['crtime'].dtstr,
                        FNrecord['mtime'].dtstr, FNrecord['atime'].dtstr, FNrecord['ctime'].dtstr)

        elif ATRrecord['type'] == 0x40:                 #  Object ID
            ObjectIDRecord = self.decodeObjectID(raw_record[read_ptr+ATRrecord['soff']:])
            record['objid'] = ObjectIDRecord
            if options.debug: print "Object ID"

        elif ATRrecord['type'] == 0x50:                 # Security descriptor
            record['sd'] = True
            if options.debug: print "Security descriptor"

        elif ATRrecord['type'] == 0x60:                 # Volume name
            record['volname'] = True
            if options.debug: print "Volume name"

        elif ATRrecord['type'] == 0x70:                 # Volume information
            if options.debug: print "Volume info attribute"
            VolumeInfoRecord = self.decodeVolumeInfo(raw_record[read_ptr+ATRrecord['soff']:])
            record['volinfo'] = VolumeInfoRecord

        elif ATRrecord['type'] == 0x80:                 # Data
            record['data'] = True
            if options.debug: print "Data attribute"

        elif ATRrecord['type'] == 0x90:                 # Index root
            record['indexroot'] = True
            if options.debug: print "Index root"

        elif ATRrecord['type'] == 0xA0:                 # Index allocation
            record['indexallocation'] = True
            if options.debug: print "Index allocation"

        elif ATRrecord['type'] == 0xB0:                 # Bitmap
            record['bitmap'] = True
            if options.debug: print "Bitmap"

        elif ATRrecord['type'] == 0xC0:                 # Reparse point
            record['reparsepoint'] = True
            if options.debug: print "Reparse point"

        elif ATRrecord['type'] == 0xD0:                 # EA Information
            record['eainfo'] = True
            if options.debug: print "EA Information"

        elif ATRrecord['type'] == 0xE0:                 # EA
            record['ea'] = True
            if options.debug: print "EA"

        elif ATRrecord['type'] == 0xF0:                 # Property set
            record['propertyset'] = True
            if options.debug: print "Property set"

        elif ATRrecord['type'] == 0x100:                 # Logged utility stream
            record['loggedutility'] = True
            if options.debug: print "Logged utility stream"

        else:
            if options.debug: print "Found an unknown attribute"

        if ATRrecord['len'] > 0:
            read_ptr = read_ptr + ATRrecord['len']
        else:
            if options.debug: print "ATRrecord->len < 0, exiting loop"
            break

    return record


def mft_to_csv(record, ret_header):
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
                       'FN Info Modify date', 'FN Info Access date',     'FN Info Entry date', 'Filename #4',
                       'FN Info Creation date', 'FN Info Modify date', 'FN Info Access date',
                       'FN Info Entry date', 'Standard Information', 'Attribute List', 'Filename',
                       'Object ID', 'Volume Name', 'Volume Info', 'Data', 'Index Root',
                       'Index Allocation', 'Bitmap', 'Reparse Point', 'EA Information', 'EA',
                       'Property Set', 'Logged Utility Stream', 'Log/Notes', 'STF FN Shift', 'uSec Zero']
        return csv_string

    if 'baad' in record:
        csv_string = ["%s" % record['recordnum'],"BAAD MFT Record"]
        return csv_string

    csv_string = [record['recordnum'], self.decodeMFTmagic(), self.decodeMFTisactive(),
                    self.decodeMFTrecordtype()]

    if 'corrupt' in record:
        tmp_string = ["%s" % record['recordnum'],"Corrupt","Corrupt","Corrupt MFT Record"]
        csv_string.extend(tmp_string)
        return csv_string

#        tmp_string = ["%d" % record['lsn']]
#        csv_string.extend(tmp_string)
    tmp_string = ["%d" % record['seq']]
    csv_string.extend(tmp_string)

    if record['fncnt'] > 0:
        csv_string.extend([str(record['fn',0]['par_ref']), str(record['fn',0]['par_seq'])])
    else:
        csv_string.extend(['NoParent', 'NoParent'])

    if record['fncnt'] > 0 and 'si' in record:
        #filenameBuffer = [FNrecord['name'], str(record['si']['crtime'].dtstr),
        filenameBuffer = [record['filename'], str(record['si']['crtime'].dtstr),
                   record['si']['mtime'].dtstr, record['si']['atime'].dtstr, record['si']['ctime'].dtstr,
                   record['fn',0]['crtime'].dtstr, record['fn',0]['mtime'].dtstr,
                   record['fn',0]['atime'].dtstr, record['fn',0]['ctime'].dtstr]
    elif 'si' in record:
        filenameBuffer = ['NoFNRecord', str(record['si']['crtime'].dtstr),
                   record['si']['mtime'].dtstr, record['si']['atime'].dtstr, record['si']['ctime'].dtstr,
                   'NoFNRecord', 'NoFNRecord', 'NoFNRecord','NoFNRecord']
    else:
        filenameBuffer = ['NoFNRecord', 'NoSIRecord', 'NoSIRecord', 'NoSIRecord', 'NoSIRecord',
                   'NoFNRecord', 'NoFNRecord', 'NoFNRecord','NoFNRecord']


    csv_string.extend(filenameBuffer)

    if 'objid' in record:
        objidBuffer = [record['objid']['objid'].objstr, record['objid']['orig_volid'].objstr,
                    record['objid']['orig_objid'].objstr, record['objid']['orig_domid'].objstr]
    else:
        objidBuffer = ['','','','']

    csv_string.extend(objidBuffer)

    # If this goes above four FN attributes, the number of columns will exceed the headers
    for i in range(1, record['fncnt']):
        filenameBuffer = [record['fn',i]['name'], record['fn',i]['crtime'].dtstr, record['fn',i]['mtime'].dtstr,
                   record['fn',i]['atime'].dtstr, record['fn',i]['ctime'].dtstr]
        csv_string.extend(filenameBuffer)
        filenameBuffer = ''

    # Pad out the remaining FN columns
    if record['fncnt'] < 2:
        tmp_string = ['','','','','','','','','','','','','','','']
    elif record['fncnt'] == 2:
        tmp_string = ['','','','','','','','','','']
    elif record['fncnt'] == 3:
        tmp_string = ['','','','','']

    csv_string.extend(tmp_string)

    # One darned big if statement, alas.
    csv_string.append('True') if 'si' in record else csv_string.append('False')
    csv_string.append('True') if 'al' in record else csv_string.append('False')
    csv_string.append('True') if record['fncnt'] > 0 else csv_string.append('False')
    csv_string.append('True') if 'objid' in record else csv_string.append('False')
    csv_string.append('True') if 'volname' in record else csv_string.append('False')
    csv_string.append('True') if 'volinfo' in record else csv_string.append('False')
    csv_string.append('True') if 'data' in record else csv_string.append('False')
    csv_string.append('True') if 'indexroot' in record else csv_string.append('False')
    csv_string.append('True') if 'indexallocation' in record else csv_string.append('False')
    csv_string.append('True') if 'bitmap' in record else csv_string.append('False')
    csv_string.append('True') if 'reparse' in record else csv_string.append('False')
    csv_string.append('True') if 'eainfo' in record else csv_string.append('False')
    csv_string.append('True') if 'ea' in record else csv_string.append('False')
    csv_string.append('True') if 'propertyset' in record else csv_string.append('False')
    csv_string.append('True') if 'loggedutility' in record else csv_string.append('False')


    if 'notes' in record:                        # Log of abnormal activity related to this record
        csv_string.append(record['notes'])
    else:
        csv_string.append('None')
        record['notes'] = ''

    if 'stf-fn-shift' in record:
        csv_string.append('Y')
    else:
        csv_string.append('N')

    if 'usec-zero' in record:
        csv_string.append('Y')
    else:
        csv_string.append('N')

    return csv_string

# MD5|name|inode|mode_as_string|UID|GID|size|atime|mtime|ctime|crtime
def mft_to_body(record, full, std):
    ' Return a MFT record in bodyfile format'

# Add option to use STD_INFO

    if record['fncnt'] > 0:

        if full == True: # Use full path
            name = record['filename']
        else:
            name = record['fn',0]['name']

        if std == True:     # Use STD_INFO
            rec_bodyfile = ("%s|%s|%s|%s|%s|%s|%s|%d|%d|%d|%d\n" %
                           ('0',name,'0','0','0','0',
                           int(record['fn',0]['real_fsize']),
                           int(record['si']['atime'].unixtime),  # was str ....
                           int(record['si']['mtime'].unixtime),
                           int(record['si']['ctime'].unixtime),
                           int(record['si']['ctime'].unixtime)))
        else:               # Use FN
            rec_bodyfile = ("%s|%s|%s|%s|%s|%s|%s|%d|%d|%d|%d\n" %
                           ('0',name,'0','0','0','0',
                           int(record['fn',0]['real_fsize']),
                           int(record['fn',0]['atime'].unixtime),
                           int(record['fn',0]['mtime'].unixtime),
                           int(record['fn',0]['ctime'].unixtime),
                           int(record['fn',0]['crtime'].unixtime)))

    else:
        if 'si' in record:
            rec_bodyfile = ("%s|%s|%s|%s|%s|%s|%s|%d|%d|%d|%d\n" %
                           ('0','No FN Record','0','0','0','0', '0',
                           int(record['si']['atime'].unixtime),  # was str ....
                           int(record['si']['mtime'].unixtime),
                           int(record['si']['ctime'].unixtime),
                           int(record['si']['ctime'].unixtime)))
        else:
            rec_bodyfile = ("%s|%s|%s|%s|%s|%s|%s|%d|%d|%d|%d\n" %
                                ('0','Corrupt Record','0','0','0','0', '0',0, 0, 0, 0))

    return (rec_bodyfile)

# l2t CSV output support
# date,time,timezone,MACB,source,sourcetype,type,user,host,short,desc,version,filename,inode,notes,format,extra
# http://code.google.com/p/log2timeline/wiki/l2t_csv

def mft_to_l2t(record):
    ' Return a MFT record in l2t CSV output format'

    if record['fncnt'] > 0:
        for i in ('atime', 'mtime', 'ctime', 'crtime'):
            (date,time) = record['fn',0][i].dtstr.split(' ')

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
                 (date, time, 'TZ', macb_str, 'FILE', 'NTFS $MFT', type_str, 'user', 'host', record['filename'], 'desc',
                  'version', record['filename'], record['seq'], record['notes'], 'format', 'extra'))

    elif 'si' in record:
        for i in ('atime', 'mtime', 'ctime', 'crtime'):
            (date,time) = record['si'][i].dtstr.split(' ')

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
                 (date, time, 'TZ', macb_str, 'FILE', 'NTFS $MFT', type_str, 'user', 'host', record['filename'], 'desc',
                  'version', record['filename'], record['seq'], record['notes'], 'format', 'extra'))

    else:
        csv_string = ("%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s\n" %
                  ('-', '-', 'TZ', 'unknown time', 'FILE', 'NTFS $MFT', 'unknown time', 'user', 'host', 'Corrupt Record', 'desc',
                  'version', 'NoFNRecord', record['seq'], '-', 'format', 'extra'))

    return csv_string


def add_note(record, s):
    if record['notes'] == '':
        record['notes'] = "%s" % s
    else:
        record['notes'] = "%s | %s |" % (self.mft_record['notes'], s)


def decodeMFTHeader(record, raw_record):

    record['magic'] = struct.unpack("<I", raw_record[:4])[0]
    record['upd_off'] = struct.unpack("<H",raw_record[4:6])[0]
    record['upd_cnt'] = struct.unpack("<H",raw_record[6:8])[0]
    record['lsn'] = struct.unpack("<d",raw_record[8:16])[0]
    record['seq'] = struct.unpack("<H",raw_record[16:18])[0]
    record['link'] = struct.unpack("<H",raw_record[18:20])[0]
    record['attr_off'] = struct.unpack("<H",raw_record[20:22])[0]
    record['flags'] = struct.unpack("<H", raw_record[22:24])[0]
    record['size'] = struct.unpack("<I",raw_record[24:28])[0]
    record['alloc_sizef'] = struct.unpack("<I",raw_record[28:32])[0]
    record['base_ref'] = struct.unpack("<Lxx",raw_record[32:38])[0]
    record['base_seq'] = struct.unpack("<H",raw_record[38:40])[0]
    record['next_attrid'] = struct.unpack("<H",raw_record[40:42])[0]
    record['f1'] = raw_record[42:44]                            # Padding
    record['recordnum'] = struct.unpack("<I", raw_record[44:48])[0]  # Number of this MFT Record
    record['fncnt'] = 0                              # Counter for number of FN attributes

def decodeMFTmagic(record):

    if record['magic'] == 0x454c4946:
        return "Good"
    elif record['magic'] == 0x44414142:
        return 'Bad'
    elif record['magic'] == 0x00000000:
        return 'Zero'
    else:
        return 'Unknown'

# decodeMFTisactive and decodeMFTrecordtype both look at the flags field in the MFT header.
# The first bit indicates if the record is active or inactive. The second bit indicates if it
# is a file or a folder.
#
# I had this coded incorrectly initially. Spencer Lynch identified and fixed the code. Many thanks!

def decodeMFTisactive(record):
    if record['flags'] & 0x0001:
        return 'Active'
    else:
        return 'Inactive'

def decodeMFTrecordtype(record):
    tmpBuffer = int(record['flags'])
    if int(record['flags']) & 0x0002:
        tmpBuffer = 'Folder'
    else:
        tmpBuffer = 'File'
    if int(record['flags']) & 0x0004:
        tmpBuffer = "%s %s" % (tmpBuffer, '+ Unknown1')
    if int(record['flags']) & 0x0008:
        tmpBuffer = "%s %s" % (tmpBuffer, '+ Unknown2')

    return tmpBuffer

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

def decodeSIAttribute(s, localtz):

    d = {}
    d['crtime'] = WindowsTime(struct.unpack("<L",s[:4])[0],struct.unpack("<L",s[4:8])[0],localtz)
    d['mtime'] = WindowsTime(struct.unpack("<L",s[8:12])[0],struct.unpack("<L",s[12:16])[0],localtz)
    d['ctime'] = WindowsTime(struct.unpack("<L",s[16:20])[0],struct.unpack("<L",s[20:24])[0],localtz)
    d['atime'] = WindowsTime(struct.unpack("<L",s[24:28])[0],struct.unpack("<L",s[28:32])[0],localtz)
    d['dos'] = struct.unpack("<I",s[32:36])[0]          # 4
    d['maxver'] = struct.unpack("<I",s[36:40])[0]       # 4
    d['ver'] = struct.unpack("<I",s[40:44])[0]          # 4
    d['class_id'] = struct.unpack("<I",s[44:48])[0]     # 4
    d['own_id'] = struct.unpack("<I",s[48:52])[0]       # 4
    d['sec_id'] = struct.unpack("<I",s[52:56])[0]       # 4
    d['quota'] = struct.unpack("<d",s[56:64])[0]        # 8
    d['usn'] = struct.unpack("<d",s[64:72])[0]          # 8 - end of date to here is 40

    return d

def decodeFNAttribute(s, localtz):

    hexFlag = False
    # File name attributes can have null dates.

    d = {}
    d['par_ref'] = struct.unpack("<Lxx", s[:6])[0]      # Parent reference nummber + seq number = 8 byte "File reference to the parent directory."
    d['par_seq'] = struct.unpack("<H",s[6:8])[0]        # Parent sequence number
    d['crtime'] = WindowsTime(struct.unpack("<L",s[8:12])[0],struct.unpack("<L",s[12:16])[0],localtz)
    d['mtime'] = WindowsTime(struct.unpack("<L",s[16:20])[0],struct.unpack("<L",s[20:24])[0],localtz)
    d['ctime'] = WindowsTime(struct.unpack("<L",s[24:28])[0],struct.unpack("<L",s[28:32])[0],localtz)
    d['atime'] = WindowsTime(struct.unpack("<L",s[32:36])[0],struct.unpack("<L",s[36:40])[0],localtz)
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
        add_note('Filename - chars converted to hex')

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
        add_note('Filename - chars converted to hex')

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

def decodeObjectID(s):

    d = {}
    d['objid'] = ObjectID(s[0:16])
    d['orig_volid'] = ObjectID(s[16:32])
    d['orig_objid'] = ObjectID(s[32:48])
    d['orig_domid'] = ObjectID(s[48:64])

    return d

def ObjectID(s):
    objstr = ''
    if s == 0:
        objstr = 'Undefined'
    else:
        objstr = "%s-%s-%s-%s-%s" % (binascii.hexlify(s[0:4]),binascii.hexlify(s[4:6]),
            binascii.hexlify(s[6:8]),binascii.hexlify(s[8:10]),binascii.hexlify(s[10:16]))

    return objstr