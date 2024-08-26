# constants.py

VERSION = '3.0'

# MFT Record Flags
RECORD_IS_DIRECTORY = 0x0002
RECORD_IS_4 = 0x0004
RECORD_IS_4_OR_8 = 0x0008

# Attribute Types
STANDARD_INFORMATION = 0x10
ATTRIBUTE_LIST = 0x20
FILE_NAME = 0x30
OBJECT_ID = 0x40
SECURITY_DESCRIPTOR = 0x50
VOLUME_NAME = 0x60
VOLUME_INFORMATION = 0x70
DATA = 0x80
INDEX_ROOT = 0x90
INDEX_ALLOCATION = 0xA0
BITMAP = 0xB0
REPARSE_POINT = 0xC0
EA_INFORMATION = 0xD0
EA = 0xE0
PROPERTY_SET = 0xF0
LOGGED_UTILITY_STREAM = 0x100

# File name namespaces
NAMESPACE_POSIX = 0
NAMESPACE_WIN32 = 1
NAMESPACE_DOS = 2
NAMESPACE_WIN32_AND_DOS = 3

# CSV Header
CSV_HEADER = [
    'Record Number', 'Good', 'Active', 'Record type',
    'Sequence Number', 'Parent File Rec. #', 'Parent File Rec. Seq. #',
    'Filename #1', 'Std Info Creation date', 'Std Info Modification date',
    'Std Info Access date', 'Std Info Entry date', 'FN Info Creation date',
    'FN Info Modification date', 'FN Info Access date', 'FN Info Entry date',
    'Object ID', 'Birth Volume ID', 'Birth Object ID', 'Birth Domain ID',
    'Filename #2', 'FN Info Creation date', 'FN Info Modify date',
    'FN Info Access date', 'FN Info Entry date', 'Filename #3', 'FN Info Creation date',
    'FN Info Modify date', 'FN Info Access date', 'FN Info Entry date', 'Filename #4',
    'FN Info Creation date', 'FN Info Modify date', 'FN Info Access date',
    'FN Info Entry date', 'Standard Information', 'Attribute List', 'Filename',
    'Object ID', 'Volume Name', 'Volume Info', 'Data', 'Index Root',
    'Index Allocation', 'Bitmap', 'Reparse Point', 'EA Information', 'EA',
    'Property Set', 'Logged Utility Stream', 'Log/Notes', 'STF FN Shift', 'uSec Zero'
]

# MFT Record Size
MFT_RECORD_SIZE = 1024