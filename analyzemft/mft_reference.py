# mft_reference.py

from typing import Dict, List, Callable
from enum import IntEnum

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
    PROPERTY_SET = 0xF0
    LOGGED_UTILITY_STREAM = 0x100

class FileNameNamespace(IntEnum):
    POSIX = 0
    WIN32 = 1
    DOS = 2
    WIN32_AND_DOS = 3

class Flags:
    MFT_RECORD: Dict[int, str] = {
        0x0001: "Record is in use",
        0x0002: "Record is a directory",
        0x0004: "Record is part of an index",
        0x0008: "Record has an index view",
    }

    STANDARD_INFORMATION: Dict[int, str] = {
        0x0001: "Read Only",
        0x0002: "Hidden",
        0x0004: "System",
        0x0020: "Archive",
        0x0040: "Device",
        0x0080: "Normal",
        0x0100: "Temporary",
        0x0200: "Sparse File",
        0x0400: "Reparse Point",
        0x0800: "Compressed",
        0x1000: "Offline",
        0x2000: "Not Content Indexed",
        0x4000: "Encrypted",
        0x10000000: "Directory",
        0x20000000: "Index View",
    }

    FILE_ATTRIBUTE: Dict[int, str] = {
        0x0001: "Read Only",
        0x0002: "Hidden",
        0x0004: "System",
        0x0010: "Directory",
        0x0020: "Archive",
        0x0040: "Device",
        0x0080: "Normal",
        0x0100: "Temporary",
        0x0200: "Sparse File",
        0x0400: "Reparse Point",
        0x0800: "Compressed",
        0x1000: "Offline",
        0x2000: "Not Content Indexed",
        0x4000: "Encrypted",
        0x8000: "Virtual",
    }

    INDEX_ENTRY: Dict[int, str] = {
        0x0001: "Child node exists",
        0x0002: "Last entry in list",
    }

class ReparsePointTags(IntEnum):
    RESERVED = 0x00000000
    MOUNT_POINT = 0x00000001
    HSM2 = 0x00000002
    HSM = 0x00000003
    SIS = 0x00000004
    WIM = 0x00000005
    CSV = 0x00000006
    DFS = 0x00000007
    FILTER_MANAGER = 0x00000008
    SYMLINK = 0x00000009
    IIS_CACHE = 0x0000000A
    DFSR = 0x0000000B
    DEDUP = 0x0000000C
    NFS = 0x0000000D
    FILE_PLACEHOLDER = 0x0000000E
    WOF = 0x0000000F
    WCI = 0x00000010
    WCI_WOF = 0x00000011
    APPEXECLINK = 0x00000012

class NTFSVersion(IntEnum):
    WINDOWS_NT = 0x100
    WINDOWS_2000 = 0x300
    WINDOWS_XP = 0x301
    WINDOWS_2003 = 0x500
    WINDOWS_VISTA = 0x600
    WINDOWS_7 = 0x601
    WINDOWS_8 = 0x602
    WINDOWS_8_1 = 0x603
    WINDOWS_10 = 0xA00

class DataRunType(IntEnum):
    SPARSE = 0x00
    NORMAL = 0x01
    COMPRESSED = 0x02
    ENCRYPTED = 0x03

def decode_flags(flags: int, flag_dict: Dict[int, str]) -> List[str]:
    return [desc for flag, desc in flag_dict.items() if flags & flag]

class MFTReference:
    @staticmethod
    def get_attribute_name(attr_type: int) -> str:
        return AttributeType(attr_type).name if attr_type in AttributeType.__members__.values() else f"Unknown (0x{attr_type:X})"

    @staticmethod
    def get_file_name_namespace(namespace: int) -> str:
        return FileNameNamespace(namespace).name if namespace in FileNameNamespace.__members__.values() else f"Unknown ({namespace})"

    @staticmethod
    def decode_mft_record_flags(flags: int) -> List[str]:
        return decode_flags(flags, Flags.MFT_RECORD)

    @staticmethod
    def decode_standard_information_flags(flags: int) -> List[str]:
        return decode_flags(flags, Flags.STANDARD_INFORMATION)

    @staticmethod
    def decode_file_attribute_flags(flags: int) -> List[str]:
        return decode_flags(flags, Flags.FILE_ATTRIBUTE)

    @staticmethod
    def get_reparse_point_tag(tag: int) -> str:
        return ReparsePointTags(tag).name if tag in ReparsePointTags.__members__.values() else f"Unknown (0x{tag:X})"

    @staticmethod
    def get_ntfs_version(version: int) -> str:
        return NTFSVersion(version).name if version in NTFSVersion.__members__.values() else f"Unknown (0x{version:X})"

    @staticmethod
    def get_data_run_type(run_type: int) -> str:
        return DataRunType(run_type).name if run_type in DataRunType.__members__.values() else f"Unknown (0x{run_type:X})"

    @staticmethod
    def decode_index_entry_flags(flags: int) -> List[str]:
        return decode_flags(flags, Flags.INDEX_ENTRY)