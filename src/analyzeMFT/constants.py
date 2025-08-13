from typing import Dict, Final
from enum import IntEnum

# =============================================================================
# VERSION INFORMATION
# =============================================================================

try:
    from importlib.metadata import version
    VERSION: Final[str] = version('analyzeMFT')
except Exception:
    VERSION: Final[str] = '3.1.1'  # Fallback version

# =============================================================================
# ENUM-LIKE CLASSES FOR BETTER TYPE SAFETY
# =============================================================================

class AttributeType(IntEnum):
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
    LOGGED_UTILITY_STREAM = 0x100

class FileNameNamespace(IntEnum):
    POSIX = 0
    WIN32 = 1
    DOS = 2
    WIN32_AND_DOS = 3

# =============================================================================
# MFT RECORD STRUCTURE CONSTANTS
# =============================================================================

# MFT Record Size
MFT_RECORD_SIZE: Final[int] = 1024

# MFT Record Magic Number
MFT_RECORD_MAGIC: Final[bytes] = b'FILE'

# MFT Record Header Offsets
MFT_RECORD_MAGIC_NUMBER_OFFSET: Final[int]              = 0
MFT_RECORD_UPDATE_SEQUENCE_OFFSET: Final[int]           = 4
MFT_RECORD_UPDATE_SEQUENCE_SIZE_OFFSET: Final[int]      = 6
MFT_RECORD_LOGFILE_SEQUENCE_NUMBER_OFFSET: Final[int]   = 8
MFT_RECORD_SEQUENCE_NUMBER_OFFSET: Final[int]           = 16
MFT_RECORD_HARD_LINK_COUNT_OFFSET: Final[int]           = 18
MFT_RECORD_FIRST_ATTRIBUTE_OFFSET: Final[int]           = 20
MFT_RECORD_FLAGS_OFFSET: Final[int]                     = 22
MFT_RECORD_USED_SIZE_OFFSET: Final[int]                 = 24
MFT_RECORD_ALLOCATED_SIZE_OFFSET: Final[int]            = 28
MFT_RECORD_FILE_REFERENCE_OFFSET: Final[int]            = 32
MFT_RECORD_NEXT_ATTRIBUTE_ID_OFFSET: Final[int]         = 40
MFT_RECORD_RECORD_NUMBER_OFFSET: Final[int]             = 44

# MFT Record Header Sizes
MFT_RECORD_MAGIC_NUMBER_SIZE: Final[int]                = 4
MFT_RECORD_UPDATE_SEQUENCE_SIZE: Final[int]             = 2
MFT_RECORD_UPDATE_SEQUENCE_SIZE_SIZE: Final[int]        = 2
MFT_RECORD_LOGFILE_SEQUENCE_NUMBER_SIZE: Final[int]     = 8
MFT_RECORD_SEQUENCE_NUMBER_SIZE: Final[int]             = 2
MFT_RECORD_HARD_LINK_COUNT_SIZE: Final[int]             = 2
MFT_RECORD_FIRST_ATTRIBUTE_SIZE: Final[int]             = 2
MFT_RECORD_FLAGS_SIZE: Final[int]                       = 2
MFT_RECORD_USED_SIZE_SIZE: Final[int]                   = 4
MFT_RECORD_ALLOCATED_SIZE_SIZE: Final[int]              = 4
MFT_RECORD_FILE_REFERENCE_SIZE: Final[int]              = 8
MFT_RECORD_NEXT_ATTRIBUTE_ID_SIZE: Final[int]           = 2
MFT_RECORD_RECORD_NUMBER_SIZE: Final[int]               = 4

# =============================================================================
# FILE RECORD FLAGS
# =============================================================================

FILE_RECORD_IN_USE: Final[int]                          = 0x0001
FILE_RECORD_IS_DIRECTORY: Final[int]                    = 0x0002
FILE_RECORD_IS_EXTENSION: Final[int]                    = 0x0004
FILE_RECORD_HAS_SPECIAL_INDEX: Final[int]               = 0x0008

# =============================================================================
# ATTRIBUTE TYPES
# =============================================================================

# Attribute type constants (using enum values)
STANDARD_INFORMATION_ATTRIBUTE: Final[int] = AttributeType.STANDARD_INFORMATION
ATTRIBUTE_LIST_ATTRIBUTE: Final[int] = AttributeType.ATTRIBUTE_LIST
FILE_NAME_ATTRIBUTE: Final[int] = AttributeType.FILE_NAME
OBJECT_ID_ATTRIBUTE: Final[int] = AttributeType.OBJECT_ID
SECURITY_DESCRIPTOR_ATTRIBUTE: Final[int] = AttributeType.SECURITY_DESCRIPTOR
VOLUME_NAME_ATTRIBUTE: Final[int] = AttributeType.VOLUME_NAME
VOLUME_INFORMATION_ATTRIBUTE: Final[int] = AttributeType.VOLUME_INFORMATION
DATA_ATTRIBUTE: Final[int] = AttributeType.DATA
INDEX_ROOT_ATTRIBUTE: Final[int] = AttributeType.INDEX_ROOT
INDEX_ALLOCATION_ATTRIBUTE: Final[int] = AttributeType.INDEX_ALLOCATION
BITMAP_ATTRIBUTE: Final[int] = AttributeType.BITMAP
REPARSE_POINT_ATTRIBUTE: Final[int] = AttributeType.REPARSE_POINT
EA_INFORMATION_ATTRIBUTE: Final[int] = AttributeType.EA_INFORMATION
EA_ATTRIBUTE: Final[int] = AttributeType.EA
LOGGED_UTILITY_STREAM_ATTRIBUTE: Final[int] = AttributeType.LOGGED_UTILITY_STREAM

# Attribute Names Mapping
ATTRIBUTE_NAMES: Final[Dict[int, str]] = {
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

# =============================================================================
# FILE ATTRIBUTES (Windows File Attribute Flags)
# =============================================================================

FILE_ATTRIBUTE_READONLY: Final[int] = 0x00000001
FILE_ATTRIBUTE_HIDDEN: Final[int] = 0x00000002
FILE_ATTRIBUTE_SYSTEM: Final[int] = 0x00000004
FILE_ATTRIBUTE_DIRECTORY: Final[int] = 0x00000010
FILE_ATTRIBUTE_ARCHIVE: Final[int] = 0x00000020
FILE_ATTRIBUTE_DEVICE: Final[int] = 0x00000040
FILE_ATTRIBUTE_NORMAL: Final[int] = 0x00000080
FILE_ATTRIBUTE_TEMPORARY: Final[int] = 0x00000100
FILE_ATTRIBUTE_SPARSE_FILE: Final[int] = 0x00000200
FILE_ATTRIBUTE_REPARSE_POINT: Final[int] = 0x00000400
FILE_ATTRIBUTE_COMPRESSED: Final[int] = 0x00000800
FILE_ATTRIBUTE_OFFLINE: Final[int] = 0x00001000
FILE_ATTRIBUTE_NOT_CONTENT_INDEXED: Final[int] = 0x00002000
FILE_ATTRIBUTE_ENCRYPTED: Final[int] = 0x00004000

# =============================================================================
# FILE NAME FLAGS
# =============================================================================

FILE_NAME_POSIX: Final[int] = 0x00
FILE_NAME_WIN32: Final[int] = 0x01
FILE_NAME_DOS: Final[int] = 0x02
FILE_NAME_WIN32_AND_DOS: Final[int] = 0x03

# Filename Namespace Mapping
FILENAME_NAMESPACE: Final[Dict[FileNameNamespace, str]] = {
    FileNameNamespace.POSIX: "POSIX",
    FileNameNamespace.WIN32: "Win32",
    FileNameNamespace.DOS: "DOS",
    FileNameNamespace.WIN32_AND_DOS: "Win32 & DOS"
}

# =============================================================================
# ATTRIBUTE STRUCTURE OFFSETS
# =============================================================================

# Standard Information Attribute
STANDARD_INFORMATION: Final[Dict[int, str]] = {
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
ATTRIBUTE_LIST: Final[Dict[int, str]] = {
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
FILE_NAME: Final[Dict[int, str]] = {
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
OBJECT_ID: Final[Dict[int, str]] = {
    0x00: "Object ID GUID",
    0x10: "Birth Volume ID GUID",
    0x20: "Birth Object ID GUID",
    0x30: "Domain ID GUID"
}

# Security Descriptor Attribute Header
SECURITY_DESCRIPTOR_HEADER: Final[Dict[int, str]] = {
    0x00: "Revision",
    0x01: "Padding",
    0x02: "Control Flags",
    0x04: "Offset to Owner SID",
    0x08: "Offset to Group SID",
    0x0C: "Offset to SACL",
    0x10: "Offset to DACL"
}

# Security Descriptor ACL
SECURITY_DESCRIPTOR_ACL: Final[Dict[int, str]] = {
    0x00: "ACL Revision",
    0x01: "Padding",
    0x02: "ACL size",
    0x04: "ACE count",
    0x06: "Padding"
}

# Security Descriptor ACE
SECURITY_DESCRIPTOR_ACE: Final[Dict[int, str]] = {
    0x00: "Type",
    0x01: "Flags",
    0x02: "Size",
    0x04: "Access mask",
    0x08: "SID"
}

# Volume Name Attribute
VOLUME_NAME: Final[Dict[int, str]] = {
    0x00: "Volume name in Unicode"
}

# Volume Information Attribute
VOLUME_INFORMATION: Final[Dict[int, str]] = {
    0x00: "Reserved (always zero?)",
    0x08: "Major version",
    0x09: "Minor version",
    0x0A: "Flags",
    0x0C: "Reserved (always zero?)"
}

# Data Attribute
DATA: Final[Dict[int, str]] = {
    0x00: "Data content"
}

# Index Root Attribute
INDEX_ROOT: Final[Dict[int, str]] = {
    0x00: "Attribute type",
    0x04: "Collation rule",
    0x08: "Bytes per index record",
    0x0C: "Clusters per index record",
    0x10: "Index node header"
}

# Index Allocation Attribute
INDEX_ALLOCATION: Final[Dict[int, str]] = {
    0x00: "Data runs"
}

# Bitmap Attribute
BITMAP: Final[Dict[int, str]] = {
    0x00: "Bit field"
}

# Reparse Point Attribute - Microsoft
REPARSE_POINT_MS: Final[Dict[int, str]] = {
    0x00: "Reparse type and flags",
    0x04: "Reparse data length",
    0x06: "Padding",
    0x08: "Reparse data"
}

# Reparse Point Attribute - Third Party
REPARSE_POINT_3RD: Final[Dict[int, str]] = {
    0x00: "Reparse type and flags",
    0x04: "Reparse data length",
    0x06: "Padding",
    0x08: "Reparse GUID",
    0x18: "Reparse data"
}

# EA Information Attribute
EA_INFORMATION: Final[Dict[int, str]] = {
    0x00: "Size of packed Extended Attributes",
    0x02: "Number of EAs with NEED_EA set",
    0x04: "Size of unpacked Extended Attributes"
}

# EA Attribute
EA: Final[Dict[int, str]] = {
    0x00: "Offset to next EA",
    0x04: "Flags",
    0x05: "Name length",
    0x06: "Value length",
    0x08: "Name",
    0x09: "Value"
}

# Logged Utility Stream
LOGGED_UTILITY_STREAM: Final[Dict[int, str]] = {
    0x00: "Any data"
}

# =============================================================================
# INDEX ENTRY FLAGS
# =============================================================================

INDEX_ENTRY_NODE: Final[int] = 0x01
INDEX_ENTRY_END: Final[int] = 0x02

# =============================================================================
# ATTRIBUTE FLAGS
# =============================================================================

ATTR_FLAG_COMPRESSED: Final[int] = 0x0001
ATTR_FLAG_ENCRYPTED: Final[int] = 0x4000
ATTR_FLAG_SPARSE: Final[int] = 0x8000

# =============================================================================
# COLLATION RULES
# =============================================================================

COLLATION_BINARY: Final[int] = 0x00
COLLATION_FILENAME: Final[int] = 0x01
COLLATION_UNICODE: Final[int] = 0x02
COLLATION_ULONG: Final[int] = 0x10
COLLATION_SID: Final[int] = 0x11
COLLATION_SECURITY_HASH: Final[int] = 0x12
COLLATION_ULONGS: Final[int] = 0x13

# =============================================================================
# DATA FORMATS
# =============================================================================

# Byte order
BYTE_ORDER: Final[str] = 'little'

# Struct format strings
STRUCT_STANDARD_INFORMATION: Final[str] = '<QQQQLLLQQQ'
STRUCT_FILE_NAME: Final[str] = '<QQQQQQLLLLBB'
STRUCT_OBJECT_ID: Final[str] = '<16s16s16s16s'

# =============================================================================
# PERFORMANCE AND OPTIMIZATION CONSTANTS
# =============================================================================

# Default chunk size for processing
DEFAULT_CHUNK_SIZE: Final[int] = 1000

# Buffer sizes for reading
DEFAULT_BUFFER_SIZE: Final[int] = 65536  # 64KB

# Hash computation defaults
DEFAULT_HASH_CHUNK_SIZE: Final[int] = 8192  # 8KB

# =============================================================================
# ERROR AND STATUS CONSTANTS
# =============================================================================

# Analysis Status Codes
ANALYSIS_STATUS_SUCCESS: Final[str] = "SUCCESS"
ANALYSIS_STATUS_ERROR: Final[str] = "ERROR"
ANALYSIS_STATUS_WARNING: Final[str] = "WARNING"
ANALYSIS_STATUS_SKIPPED: Final[str] = "SKIPPED"

# Record Status Descriptions
RECORD_STATUS_DESCRIPTIONS: Final[Dict[int, str]] = {
    0x0000: "Unused Record",
    0x0001: "Active File",
    0x0002: "Directory",
    0x0003: "Active Directory",
}

# =============================================================================
# CSV OUTPUT CONSTANTS
# =============================================================================

CSV_HEADER: Final[list] = [
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

# =============================================================================
# VALIDATION AND UTILITY FUNCTIONS
# =============================================================================

def is_valid_attribute_type(attr_type: int) -> bool:
    """Check if the given attribute type is valid."""
    return attr_type in ATTRIBUTE_NAMES

def get_attribute_name(attr_type: int) -> str:
    """Get the name of an attribute type."""
    return ATTRIBUTE_NAMES.get(attr_type, f"UNKNOWN_ATTRIBUTE_{attr_type:02X}")

def is_directory_record(flags: int) -> bool:
    """Check if the record is a directory."""
    return bool(flags & FILE_RECORD_IS_DIRECTORY)

def is_record_in_use(flags: int) -> bool:
    """Check if the record is in use."""
    return bool(flags & FILE_RECORD_IN_USE)

def get_filename_namespace_name(namespace_id: int) -> str:
    """Get the name of a filename namespace."""
    try:
        namespace = FileNameNamespace(namespace_id)
        return FILENAME_NAMESPACE[namespace]
    except ValueError:
        return f"UNKNOWN_NAMESPACE_{namespace_id}"
