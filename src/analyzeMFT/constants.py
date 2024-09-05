VERSION = '3.0.6.3'

# File Record Flags
FILE_RECORD_IN_USE = 0x0001
FILE_RECORD_IS_DIRECTORY = 0x0002
FILE_RECORD_IS_EXTENSION = 0x0004
FILE_RECORD_HAS_SPECIAL_INDEX = 0x0008

# Attribute Types
STANDARD_INFORMATION_ATTRIBUTE = 0x10
ATTRIBUTE_LIST_ATTRIBUTE = 0x20
FILE_NAME_ATTRIBUTE = 0x30
OBJECT_ID_ATTRIBUTE = 0x40
SECURITY_DESCRIPTOR_ATTRIBUTE = 0x50
VOLUME_NAME_ATTRIBUTE = 0x60
VOLUME_INFORMATION_ATTRIBUTE = 0x70
DATA_ATTRIBUTE = 0x80
INDEX_ROOT_ATTRIBUTE = 0x90
INDEX_ALLOCATION_ATTRIBUTE = 0xA0
BITMAP_ATTRIBUTE = 0xB0
REPARSE_POINT_ATTRIBUTE = 0xC0
EA_INFORMATION_ATTRIBUTE = 0xD0
EA_ATTRIBUTE = 0xE0
LOGGED_UTILITY_STREAM_ATTRIBUTE = 0x100

# Attribute Names
ATTRIBUTE_NAMES = {
    STANDARD_INFORMATION_ATTRIBUTE: "$STANDARD_INFORMATION",
    ATTRIBUTE_LIST_ATTRIBUTE: "$ATTRIBUTE_LIST",
    FILE_NAME_ATTRIBUTE: "$FILE_NAME",
    OBJECT_ID_ATTRIBUTE: "$OBJECT_ID",
    SECURITY_DESCRIPTOR_ATTRIBUTE: "$SECURITY_DESCRIPTOR",
    VOLUME_NAME_ATTRIBUTE: "$VOLUME_NAME",
    VOLUME_INFORMATION_ATTRIBUTE: "$VOLUME_INFORMATION",
    DATA_ATTRIBUTE: "$DATA",
    INDEX_ROOT_ATTRIBUTE: "$INDEX_ROOT",
    INDEX_ALLOCATION_ATTRIBUTE: "$INDEX_ALLOCATION",
    BITMAP_ATTRIBUTE: "$BITMAP",
    REPARSE_POINT_ATTRIBUTE: "$REPARSE_POINT",
    EA_INFORMATION_ATTRIBUTE: "$EA_INFORMATION",
    EA_ATTRIBUTE: "$EA",
    LOGGED_UTILITY_STREAM_ATTRIBUTE: "$LOGGED_UTILITY_STREAM"
}

# Standard Information Attribute
STANDARD_INFORMATION = {
    0x00: "Creation time",
    0x08: "Last modification time",
    0x10: "Last change time",
    0x18: "Last access time",
    0x20: "File attributes",
    0x24: "Maximum versions",
    0x28: "Version number",
    0x2C: "Class ID",
    0x30: "Owner ID",
    0x34: "Security ID",
    0x38: "Quota charged",
    0x40: "Update sequence number (USN)"
}

# Attribute List
ATTRIBUTE_LIST = {
    0x00: "Attribute type",
    0x04: "Record length",
    0x06: "Name length (N)",
    0x07: "Offset to Name",
    0x08: "Starting VCN",
    0x10: "Base File Reference of the attribute",
    0x18: "Attribute ID",
    0x1A: "Name in Unicode (if N > 0)"
}

# File Name Attribute
FILE_NAME = {
    0x00: "Parent directory file reference",
    0x08: "Creation time",
    0x10: "Last modification time",
    0x18: "Last change time",
    0x20: "Last access time",
    0x28: "Allocated size",
    0x30: "Real size",
    0x38: "Flags",
    0x3C: "Used by EAs and Reparse",
    0x40: "Filename length in characters",
    0x41: "Filename namespace",
    0x42: "Filename (Unicode)"
}

# Object ID Attribute
OBJECT_ID = {
    0x00: "Object ID GUID",
    0x10: "Birth Volume ID GUID",
    0x20: "Birth Object ID GUID",
    0x30: "Domain ID GUID"
}

# Security Descriptor Attribute Header
SECURITY_DESCRIPTOR_HEADER = {
    0x00: "Revision",
    0x01: "Padding",
    0x02: "Control Flags",
    0x04: "Offset to Owner SID",
    0x08: "Offset to Group SID",
    0x0C: "Offset to SACL",
    0x10: "Offset to DACL"
}

# Security Descriptor ACL
SECURITY_DESCRIPTOR_ACL = {
    0x00: "ACL Revision",
    0x01: "Padding",
    0x02: "ACL size",
    0x04: "ACE count",
    0x06: "Padding"
}

# Security Descriptor ACE
SECURITY_DESCRIPTOR_ACE = {
    0x00: "Type",
    0x01: "Flags",
    0x02: "Size",
    0x04: "Access mask",
    0x08: "SID"
}

# Volume Name Attribute
VOLUME_NAME = {
    0x00: "Volume name in Unicode"
}

# Volume Information Attribute
VOLUME_INFORMATION = {
    0x00: "Reserved (always zero?)",
    0x08: "Major version",
    0x09: "Minor version",
    0x0A: "Flags",
    0x0C: "Reserved (always zero?)"
}

# Data Attribute
DATA = {
    0x00: "Data content"
}

# Index Root Attribute
INDEX_ROOT = {
    0x00: "Attribute type",
    0x04: "Collation rule",
    0x08: "Bytes per index record",
    0x0C: "Clusters per index record",
    0x10: "Index node header"
}

# Index Allocation Attribute
INDEX_ALLOCATION = {
    0x00: "Data runs"
}

# Bitmap Attribute
BITMAP = {
    0x00: "Bit field"
}

# Reparse Point Attribute - Microsoft
REPARSE_POINT_MS = {
    0x00: "Reparse type and flags",
    0x04: "Reparse data length",
    0x06: "Padding",
    0x08: "Reparse data"
}

# Reparse Point Attribute - Third Party
REPARSE_POINT_3RD = {
    0x00: "Reparse type and flags",
    0x04: "Reparse data length",
    0x06: "Padding",
    0x08: "Reparse GUID",
    0x18: "Reparse data"
}

# EA Information Attribute
EA_INFORMATION = {
    0x00: "Size of packed Extended Attributes",
    0x02: "Number of EAs with NEED_EA set",
    0x04: "Size of unpacked Extended Attributes"
}

# EA Attribute
EA = {
    0x00: "Offset to next EA",
    0x04: "Flags",
    0x05: "Name length",
    0x06: "Value length",
    0x08: "Name",
    0x09: "Value"
}

# Logged Utility Stream
LOGGED_UTILITY_STREAM = {
    0x00: "Any data"
}

# Filename Namespaces
FILENAME_NAMESPACE = {
    0: "POSIX",
    1: "Win32",
    2: "DOS",
    3: "Win32 & DOS"
}

# Index Entry Flags
INDEX_ENTRY_NODE = 0x01
INDEX_ENTRY_END = 0x02

# MFT Record Size
MFT_RECORD_SIZE = 1024

# Attribute Flags
ATTR_FLAG_COMPRESSED = 0x0001
ATTR_FLAG_ENCRYPTED = 0x4000
ATTR_FLAG_SPARSE = 0x8000

# Collation Rules
COLLATION_BINARY = 0x00
COLLATION_FILENAME = 0x01
COLLATION_UNICODE = 0x02
COLLATION_ULONG = 0x10
COLLATION_SID = 0x11
COLLATION_SECURITY_HASH = 0x12
COLLATION_ULONGS = 0x13

# Byte order
BYTE_ORDER = 'little'

# Struct format strings
STRUCT_STANDARD_INFORMATION = '<QQQQLLLQQQ'
STRUCT_FILE_NAME = '<QQQQQQLLLLBB'
STRUCT_OBJECT_ID = '<16s16s16s16s'

# MFT Record header offsets and sizes
MFT_RECORD_MAGIC_NUMBER_OFFSET = 0
MFT_RECORD_UPDATE_SEQUENCE_OFFSET = 4
MFT_RECORD_UPDATE_SEQUENCE_SIZE_OFFSET = 6
MFT_RECORD_LOGFILE_SEQUENCE_NUMBER_OFFSET = 8
MFT_RECORD_SEQUENCE_NUMBER_OFFSET = 16
MFT_RECORD_HARD_LINK_COUNT_OFFSET = 18
MFT_RECORD_FIRST_ATTRIBUTE_OFFSET = 20
MFT_RECORD_FLAGS_OFFSET = 22
MFT_RECORD_USED_SIZE_OFFSET = 24
MFT_RECORD_ALLOCATED_SIZE_OFFSET = 28
MFT_RECORD_FILE_REFERENCE_OFFSET = 32
MFT_RECORD_NEXT_ATTRIBUTE_ID_OFFSET = 40
MFT_RECORD_RECORD_NUMBER_OFFSET = 44

# MFT Record header sizes
MFT_RECORD_MAGIC_NUMBER_SIZE = 4
MFT_RECORD_UPDATE_SEQUENCE_SIZE = 2
MFT_RECORD_UPDATE_SEQUENCE_SIZE_SIZE = 2
MFT_RECORD_LOGFILE_SEQUENCE_NUMBER_SIZE = 8
MFT_RECORD_SEQUENCE_NUMBER_SIZE = 2
MFT_RECORD_HARD_LINK_COUNT_SIZE = 2
MFT_RECORD_FIRST_ATTRIBUTE_SIZE = 2
MFT_RECORD_FLAGS_SIZE = 2
MFT_RECORD_USED_SIZE_SIZE = 4
MFT_RECORD_ALLOCATED_SIZE_SIZE = 4
MFT_RECORD_FILE_REFERENCE_SIZE = 8
MFT_RECORD_NEXT_ATTRIBUTE_ID_SIZE = 2
MFT_RECORD_RECORD_NUMBER_SIZE = 4

# MFT Record magic number
MFT_RECORD_MAGIC = b'FILE'

CSV_HEADER = [
    # Basic Record Information
    'Record Number', 
    'Record Status',  # Instead of 'Good'/'Bad'
    'Record Type',    # Instead of 'Active'/'Inactive'
    'File Type',      # Instead of 'Record type'
    'Sequence Number',
    'Parent Record Number',
    'Parent Record Sequence Number',
    
    # File Information
    'Filename',
    'Filepath',
    
    # Standard Information Times
    'SI Creation Time',
    'SI Modification Time',
    'SI Access Time',
    'SI Entry Time',
    
    # File Name Attribute Times
    'FN Creation Time',
    'FN Modification Time',
    'FN Access Time',
    'FN Entry Time',
    
    # Object ID Information
    'Object ID',
    'Birth Volume ID',
    'Birth Object ID',
    'Birth Domain ID',
    
    # Attribute Presence Flags
    'Has Standard Information',
    'Has Attribute List',
    'Has File Name',
    'Has Volume Name',
    'Has Volume Information',
    'Has Data',
    'Has Index Root',
    'Has Index Allocation',
    'Has Bitmap',
    'Has Reparse Point',
    'Has EA Information',
    'Has EA',
    'Has Logged Utility Stream',
    
    # Detailed Attribute Information
    'Attribute List Details',
    'Security Descriptor',
    'Volume Name',
    'Volume Information',
    'Data Attribute',
    'Index Root',
    'Index Allocation',
    'Bitmap',
    'Reparse Point',
    'EA Information',
    'EA',
    'Logged Utility Stream',
    
    # Hash Information (if computed)
    'MD5',
    'SHA256',
    'SHA512',
    'CRC32'
]