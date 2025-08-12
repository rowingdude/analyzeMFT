import pytest
import struct
import os
from unittest.mock import patch, MagicMock
from src.analyzeMFT.mft_record import MftRecord
from src.analyzeMFT.constants import *
from src.analyzeMFT.windows_time import WindowsTime
import uuid

@pytest.fixture
def mock_raw_record():
    record = bytearray(MFT_RECORD_SIZE)
    struct.pack_into("<I", record, 0, int.from_bytes(MFT_RECORD_MAGIC, BYTE_ORDER))
    struct.pack_into("<H", record, 4, 42)
    struct.pack_into("<H", record, 6, 3)
    struct.pack_into("<Q", record, 8, 12345)
    struct.pack_into("<H", record, 16, 1)
    struct.pack_into("<H", record, 18, 1)
    struct.pack_into("<H", record, 20, 56)
    struct.pack_into("<H", record, 22, FILE_RECORD_IN_USE)
    struct.pack_into("<I", record, 24, MFT_RECORD_SIZE)
    struct.pack_into("<I", record, 28, MFT_RECORD_SIZE)
    struct.pack_into("<Q", record, 32, 0)
    struct.pack_into("<H", record, 40, 2)
    struct.pack_into("<I", record, 44, 5)
    return record

@pytest.fixture
def mft_record(mock_raw_record):
    return MftRecord(mock_raw_record)

def test_mft_record_initialization(mft_record):
    assert mft_record.magic == int.from_bytes(MFT_RECORD_MAGIC, BYTE_ORDER)
    assert mft_record.upd_off == 42
    assert mft_record.upd_cnt == 3
    assert mft_record.lsn == 12345
    assert mft_record.seq == 1
    assert mft_record.link == 1
    assert mft_record.attr_off == 56
    assert mft_record.flags == FILE_RECORD_IN_USE
    assert mft_record.size == MFT_RECORD_SIZE
    assert mft_record.alloc_sizef == MFT_RECORD_SIZE
    assert mft_record.base_ref == 0
    assert mft_record.next_attrid == 2
    assert mft_record.recordnum == 5

def test_parse_si_attribute(mft_record):
    attr_header = struct.pack("<IBBHHHH", 
        0x10,
        72,
        0,
        0,
        24,
        0,
        0
    ) + b'\x00' * 10
    
    si_content = struct.pack("<QQQQLLLQQQ", 
        131092560000000000, 131092560010000000, 131092560020000000, 131092560030000000,
        0x80, 0, 0, 0, 0, 0)
    
    si_data = attr_header + si_content
    offset = 56
    mft_record.raw_record[offset:offset+len(si_data)] = si_data
    
    mft_record.parse_si_attribute(offset)
    
    assert isinstance(mft_record.si_times['crtime'], WindowsTime)
    assert mft_record.si_times['crtime'].dt.year == 2016
    assert mft_record.si_times['mtime'].dt > mft_record.si_times['crtime'].dt
    assert mft_record.si_times['ctime'].dt > mft_record.si_times['mtime'].dt
    assert mft_record.si_times['atime'].dt > mft_record.si_times['ctime'].dt

def test_parse_fn_attribute(mft_record):
    attr_header = struct.pack("<IBBHHHH", 
        0x30,
        90,
        0,
        0,
        24,
        0,
        0
    ) + b'\x00' * 10
    
    fn_content = struct.pack("<QQQQQQQLLBB", 
        5, 131092560000000000, 131092560010000000, 131092560020000000, 131092560030000000,
        1024, 1024, FILE_RECORD_IN_USE, 0, 8, 0) + "test.txt".encode('utf-16le')
    
    fn_data = attr_header + fn_content
    offset = 56
    mft_record.raw_record[offset:offset+len(fn_data)] = fn_data
    
    mft_record.parse_fn_attribute(offset)
    
    assert mft_record.filename == "test.txt"
    assert mft_record.filesize == 1024
    assert mft_record.parent_ref == 5
    assert mft_record.fn_times['crtime'].dt.year == 2016
    assert mft_record.fn_times['mtime'].dt > mft_record.fn_times['crtime'].dt
    assert mft_record.fn_times['ctime'].dt > mft_record.fn_times['mtime'].dt
    assert mft_record.fn_times['atime'].dt > mft_record.fn_times['ctime'].dt

def test_parse_object_id_attribute(mft_record):
    obj_id = uuid.uuid4().bytes
    birth_volume_id = uuid.uuid4().bytes
    birth_object_id = uuid.uuid4().bytes
    birth_domain_id = uuid.uuid4().bytes
    attr_header = struct.pack("<IBBHHHH", 
        0x40,
        88,
        0,
        0,
        24,
        0,
        0
    ) + b'\x00' * 10
    
    obj_id_content = obj_id + birth_volume_id + birth_object_id + birth_domain_id
    obj_id_data = attr_header + obj_id_content
    
    offset = 56
    mft_record.raw_record[offset:offset+len(obj_id_data)] = obj_id_data
    
    mft_record.parse_object_id(offset)
    
    assert uuid.UUID(mft_record.object_id).bytes_le == obj_id
    assert uuid.UUID(mft_record.birth_volume_id).bytes_le == birth_volume_id
    assert uuid.UUID(mft_record.birth_object_id).bytes_le == birth_object_id
    assert uuid.UUID(mft_record.birth_domain_id).bytes_le == birth_domain_id

def test_parse_data_attribute_resident(mft_record):
    data_content = b"This is the content of test.txt"
    offset = 56
    add_attribute(mft_record.raw_record, offset, DATA_ATTRIBUTE, data_content)
    
    mft_record.parse_data(offset)
    
    assert mft_record.data_attribute['name'] == ''
    assert mft_record.data_attribute['non_resident'] == False
    assert mft_record.data_attribute['content_size'] == len(data_content)

def test_parse_data_attribute_non_resident(mft_record):
    offset = 56
    struct.pack_into('<I', mft_record.raw_record, offset, DATA_ATTRIBUTE)
    struct.pack_into('<I', mft_record.raw_record, offset + 4, 32)
    struct.pack_into('<B', mft_record.raw_record, offset + 8, 1)
    struct.pack_into('<B', mft_record.raw_record, offset + 9, 0)
    struct.pack_into('<H', mft_record.raw_record, offset + 10, 24)
    struct.pack_into('<H', mft_record.raw_record, offset + 12, 0)
    struct.pack_into('<H', mft_record.raw_record, offset + 14, 0)
    struct.pack_into('<Q', mft_record.raw_record, offset + 16, 1000)
    struct.pack_into('<Q', mft_record.raw_record, offset + 24, 2000)
    
    mft_record.parse_data(offset)
    
    assert mft_record.data_attribute['name'] == ''
    assert mft_record.data_attribute['non_resident'] == True
    assert mft_record.data_attribute['start_vcn'] == 1000
    assert mft_record.data_attribute['last_vcn'] == 2000

def test_parse_index_root(mft_record):
    ir_data = struct.pack("<LLLLBBHH", FILE_NAME_ATTRIBUTE, COLLATION_FILENAME, 4096, 1, 1, 0, 0, 0)
    offset = 56
    add_attribute(mft_record.raw_record, offset, INDEX_ROOT_ATTRIBUTE, ir_data)
    
    mft_record.parse_index_root(offset)
    
    assert mft_record.index_root['attr_type'] == FILE_NAME_ATTRIBUTE
    assert mft_record.index_root['collation_rule'] == COLLATION_FILENAME
    assert mft_record.index_root['index_alloc_size'] == 4096
    assert mft_record.index_root['clusters_per_index'] == 1

def test_parse_index_allocation(mft_record):
    ia_data = struct.pack("<H", 16) + b'\x00' * 14
    offset = 56
    add_attribute(mft_record.raw_record, offset, INDEX_ALLOCATION_ATTRIBUTE, ia_data)
    
    mft_record.parse_index_allocation(offset)
    
    assert mft_record.index_allocation['data_runs_offset'] == 16

def test_parse_bitmap(mft_record):
    bitmap_data = struct.pack("<L", 8) + b'\xff' * 8
    offset = 56
    add_attribute(mft_record.raw_record, offset, BITMAP_ATTRIBUTE, bitmap_data)
    
    mft_record.parse_bitmap(offset)
    
    assert mft_record.bitmap['size'] == 8
    assert mft_record.bitmap['data'] == b'\xff' * 8

def test_parse_reparse_point(mft_record):
    reparse_data = b"Reparse data"
    rp_data = struct.pack("<LH", 0x80000000, len(reparse_data)) + b'\x00' * 2 + reparse_data
    offset = 56
    add_attribute(mft_record.raw_record, offset, REPARSE_POINT_ATTRIBUTE, rp_data)
    
    mft_record.parse_reparse_point(offset)
    
    assert mft_record.reparse_point['reparse_tag'] == 0x80000000
    assert mft_record.reparse_point['data_length'] == len(reparse_data)
    assert mft_record.reparse_point['data'] == reparse_data

def test_parse_ea_information(mft_record):
    eai_data = struct.pack("<LL", 256, 2)
    offset = 56
    add_attribute(mft_record.raw_record, offset, EA_INFORMATION_ATTRIBUTE, eai_data)
    
    mft_record.parse_ea_information(offset)
    
    assert mft_record.ea_information['ea_size'] == 256
    assert mft_record.ea_information['ea_count'] == 2

def test_parse_ea(mft_record):
    ea_data = struct.pack("<LBBH", 0, 0, 4, 5) + b"name" + b"value"
    offset = 56
    add_attribute(mft_record.raw_record, offset, EA_ATTRIBUTE, ea_data)
    
    mft_record.parse_ea(offset)
    
    assert mft_record.ea['next_entry_offset'] == 0
    assert mft_record.ea['flags'] == 0
    assert mft_record.ea['name'] == "name"
    assert mft_record.ea['value'] == b"value"

def test_parse_logged_utility_stream(mft_record):
    stream_data = b"Utility stream"
    lus_data = struct.pack("<Q", len(stream_data)) + stream_data
    offset = 56
    add_attribute(mft_record.raw_record, offset, LOGGED_UTILITY_STREAM_ATTRIBUTE, lus_data)
    
    mft_record.parse_logged_utility_stream(offset)
    
    assert mft_record.logged_utility_stream['size'] == len(stream_data)
    assert mft_record.logged_utility_stream['data'] == stream_data

def test_parse_volume_name(mft_record):
    volume_name = "TestVolume"
    vn_data = struct.pack("<H", len(volume_name)) + volume_name.encode('utf-16le')
    offset = 56
    add_attribute(mft_record.raw_record, offset, VOLUME_NAME_ATTRIBUTE, vn_data)
    
    mft_record.parse_volume_name(offset)
    
    assert mft_record.volume_name == "TestVolume"

def test_parse_volume_information(mft_record):
    vi_data = b'\x00' * 8 + struct.pack('<BBH', 3, 1, 0x0001)
    offset = 56
    add_attribute(mft_record.raw_record, offset, VOLUME_INFORMATION_ATTRIBUTE, vi_data)
    
    mft_record.parse_volume_information(offset)
    
    assert mft_record.volume_info['major_version'] == 3
    assert mft_record.volume_info['minor_version'] == 1
    assert mft_record.volume_info['flags'] == 0x0001

def test_to_csv(mft_record):
    mft_record.filename = "test.txt"
    mft_record.filesize = 1024
    mft_record.flags = FILE_RECORD_IN_USE
    
    csv_row = mft_record.to_csv()
    
    assert csv_row[0] == 5
    assert csv_row[1] == "Valid"
    assert csv_row[2] == "In Use"
    assert csv_row[3] == "File"
    assert csv_row[7] == "test.txt"
    assert csv_row[17] == ""
    assert csv_row[18] == ""
    assert csv_row[19] == ""
    assert csv_row[20] == ""
def test_compute_hashes(mft_record):
    mft_record.compute_hashes()
    
    assert len(mft_record.md5) == 32
    assert len(mft_record.sha256) == 64
    assert len(mft_record.sha512) == 128
    assert len(mft_record.crc32) == 8

def test_get_file_type(mft_record):
    mft_record.flags = FILE_RECORD_IS_DIRECTORY
    assert mft_record.get_file_type() == "Directory"
    
    mft_record.flags = FILE_RECORD_IS_EXTENSION
    assert mft_record.get_file_type() == "Extension"
    
    mft_record.flags = FILE_RECORD_HAS_SPECIAL_INDEX
    assert mft_record.get_file_type() == "Special Index"
    
    mft_record.flags = FILE_RECORD_IN_USE
    assert mft_record.get_file_type() == "File"

def test_get_parent_record_num(mft_record):
    mft_record.parent_ref = (5 << 48) | 1234
    assert mft_record.get_parent_record_num() == 1234

def test_parse_security_descriptor(mft_record):
    sd_data = struct.pack("<BBHLLLL", 1, 0, 0x8004, 20, 40, 60, 80) + os.urandom(64)
    offset = 56
    add_attribute(mft_record.raw_record, offset, SECURITY_DESCRIPTOR_ATTRIBUTE, sd_data)
    
    mft_record.parse_security_descriptor(offset)
    
    assert mft_record.security_descriptor['revision'] == 1
    assert mft_record.security_descriptor['control'] == 0x8004
    assert mft_record.security_descriptor['owner_offset'] == 20
    assert mft_record.security_descriptor['group_offset'] == 40
    assert mft_record.security_descriptor['sacl_offset'] == 60
    assert mft_record.security_descriptor['dacl_offset'] == 80

def test_parse_attribute_list(mft_record):
    entry1 = struct.pack("<LHHBBQQ", 0x10, 24, 0, 0, 24, 0, 0, 1)
    entry2 = struct.pack("<LHHBBQQ", 0x30, 24, 0, 0, 24, 0, 0, 2)
    attr_list_data = entry1 + entry2
    offset = 56
    add_attribute(mft_record.raw_record, offset, ATTRIBUTE_LIST_ATTRIBUTE, attr_list_data)
    
    mft_record.parse_attribute_list(offset)
    
    assert len(mft_record.attribute_list) == 2
    assert mft_record.attribute_list[0]['type'] == 0x10
    assert mft_record.attribute_list[0]['reference'] == 1
    assert mft_record.attribute_list[1]['type'] == 0x30
    assert mft_record.attribute_list[1]['reference'] == 2

def test_parse_multiple_attributes(mft_record):
    offset = 56
    si_data = struct.pack("<QQQQLLLQQQ", 
        131092560000000000, 131092560000000001, 131092560000000002, 131092560000000003,
        0x80, 0, 0, 0, 0, 0)
    offset = add_attribute(mft_record.raw_record, offset, STANDARD_INFORMATION_ATTRIBUTE, si_data)
    fn_data = struct.pack("<QQQQQQLLLLBB", 
        5, 131000000000000, 131000000000001, 131000000000002, 131000000000003,
        1024, 1024, FILE_RECORD_IN_USE, 0, 8, 0) + "test.txt".encode('utf-16le')
    offset = add_attribute(mft_record.raw_record, offset, FILE_NAME_ATTRIBUTE, fn_data)
    data_content = b"This is the content of test.txt"
    offset = add_attribute(mft_record.raw_record, offset, DATA_ATTRIBUTE, data_content)
    
    mft_record.parse_record()
    
    assert STANDARD_INFORMATION_ATTRIBUTE in mft_record.attribute_types
    assert FILE_NAME_ATTRIBUTE in mft_record.attribute_types
    assert DATA_ATTRIBUTE in mft_record.attribute_types
    assert mft_record.filename == "test.txt"
    assert mft_record.filesize == 1024
    assert mft_record.data_attribute['content_size'] == len(data_content)

def test_parse_directory_record(mft_record):
    mft_record.flags = FILE_RECORD_IN_USE | FILE_RECORD_IS_DIRECTORY
    offset = 56
    ir_data = struct.pack("<LLLLBBHH", FILE_NAME_ATTRIBUTE, COLLATION_FILENAME, 4096, 1, 1, 0, 0, 0)
    offset = add_attribute(mft_record.raw_record, offset, INDEX_ROOT_ATTRIBUTE, ir_data)
    ia_data = struct.pack("<H", 16) + os.urandom(496)
    offset = add_attribute(mft_record.raw_record, offset, INDEX_ALLOCATION_ATTRIBUTE, ia_data)
    bitmap_data = struct.pack("<L", 8) + b'\xff' * 8
    offset = add_attribute(mft_record.raw_record, offset, BITMAP_ATTRIBUTE, bitmap_data)
    
    mft_record.parse_record()
    
    assert mft_record.get_file_type() == "Directory"
    assert INDEX_ROOT_ATTRIBUTE in mft_record.attribute_types
    assert INDEX_ALLOCATION_ATTRIBUTE in mft_record.attribute_types
    assert BITMAP_ATTRIBUTE in mft_record.attribute_types
    assert mft_record.index_root['attr_type'] == FILE_NAME_ATTRIBUTE
    assert mft_record.index_allocation['data_runs_offset'] == 16
    assert mft_record.bitmap['size'] == 8

def test_parse_volume_record(mft_record):
    mft_record.recordnum = 3
    offset = 56
    vn_data = "TestVolume".encode('utf-16le')
    offset = add_attribute(mft_record.raw_record, offset, VOLUME_NAME_ATTRIBUTE, vn_data)
    vi_data = struct.pack('<BBBBBBH', 0, 0, 0, 0, 3, 1, 0x0001)
    offset = add_attribute(mft_record.raw_record, offset, VOLUME_INFORMATION_ATTRIBUTE, vi_data)
    
    mft_record.parse_record()
    
    assert VOLUME_NAME_ATTRIBUTE in mft_record.attribute_types
    assert VOLUME_INFORMATION_ATTRIBUTE in mft_record.attribute_types
    assert mft_record.volume_name == "TestVolume"
    assert mft_record.volume_info['major_version'] == 3
    assert mft_record.volume_info['minor_version'] == 1
    assert mft_record.volume_info['flags'] == 0x0001

def test_parse_reparse_point_record(mft_record):
    offset = 56
    rp_data = struct.pack("<LH", 0x80000000, 12) + b'\x00' * 2 + b"Reparse data"
    offset = add_attribute(mft_record.raw_record, offset, REPARSE_POINT_ATTRIBUTE, rp_data)
    
    mft_record.parse_record()
    
    assert REPARSE_POINT_ATTRIBUTE in mft_record.attribute_types
    assert mft_record.reparse_point['reparse_tag'] == 0x80000000
    assert mft_record.reparse_point['data_length'] == 12
    assert mft_record.reparse_point['data'] == b'\x00' * 2 + b"Reparse data"

def test_parse_extended_attributes(mft_record):
    offset = 56
    eai_data = struct.pack("<LL", 256, 2)
    offset = add_attribute(mft_record.raw_record, offset, EA_INFORMATION_ATTRIBUTE, eai_data)
    ea_data = struct.pack("<LBBH", 0, 0, 4, 5) + b"name" + b"value"
    offset = add_attribute(mft_record.raw_record, offset, EA_ATTRIBUTE, ea_data)
    
    mft_record.parse_record()
    
    assert EA_INFORMATION_ATTRIBUTE in mft_record.attribute_types
    assert EA_ATTRIBUTE in mft_record.attribute_types
    assert mft_record.ea_information['ea_size'] == 256
    assert mft_record.ea_information['ea_count'] == 2
    assert mft_record.ea['name'] == "name"
    assert mft_record.ea['value'] == b"value"

def test_parse_logged_utility_stream(mft_record):
    offset = 56
    stream_data = b"Utility stream"
    lus_data = struct.pack("<Q", len(stream_data)) + stream_data
    offset = add_attribute(mft_record.raw_record, offset, LOGGED_UTILITY_STREAM_ATTRIBUTE, lus_data)
    
    mft_record.parse_record()
    
    assert LOGGED_UTILITY_STREAM_ATTRIBUTE in mft_record.attribute_types
    assert mft_record.logged_utility_stream['size'] == len(stream_data)
    assert mft_record.logged_utility_stream['data'] == stream_data

def add_attribute(record, offset, attr_type, data):
    attr_len = len(data) + 24
    struct.pack_into('<I', record, offset, attr_type)
    struct.pack_into('<I', record, offset + 4, attr_len)
    struct.pack_into('<B', record, offset + 8, 0)
    struct.pack_into('<B', record, offset + 9, 0)
    struct.pack_into('<H', record, offset + 10, 24)
    struct.pack_into('<H', record, offset + 12, 0)
    struct.pack_into('<H', record, offset + 14, 0)
    struct.pack_into('<L', record, offset + 16, len(data))
    struct.pack_into('<H', record, offset + 20, 24)
    record[offset + 24:offset + 24 + len(data)] = data
    return offset + attr_len


def test_parse_corrupted_record():
    corrupted_record = b'\x00' * MFT_RECORD_SIZE
    record = MftRecord(corrupted_record)
    assert record.magic != int.from_bytes(MFT_RECORD_MAGIC, BYTE_ORDER)

def test_parse_incomplete_record():
    incomplete_record = b'FILE' + b'\x00' * 100
    with pytest.raises(Exception):
        MftRecord(incomplete_record)

def test_parse_large_attribute():
    large_attr_record = bytearray(MFT_RECORD_SIZE)
    large_attr_record[:4] = MFT_RECORD_MAGIC
    large_attr_data = b'\x80' + struct.pack('<I', MFT_RECORD_SIZE - 24) + b'\x00' * (MFT_RECORD_SIZE - 28)
    large_attr_record[24:] = large_attr_data
    
    record = MftRecord(large_attr_record)
    assert DATA_ATTRIBUTE in record.attribute_types