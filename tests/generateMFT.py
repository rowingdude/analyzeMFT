import struct
import random
import os
import uuid
from datetime import datetime, timedelta
from constants import *

def windows_time(dt):
    """Convert a datetime object to Windows filetime"""
    unix_time = int((dt - datetime(1970, 1, 1)).total_seconds())
    return (unix_time + 11644473600) * 10000000

def create_mft_record(record_number, flags, filename):
    record = bytearray(MFT_RECORD_SIZE)
    
    # FILE signature
    record[0:4] = MFT_RECORD_MAGIC
    
    # Sequence number
    struct.pack_into('<H', record, 16, random.randint(1, 100))
    
    # Link count
    struct.pack_into('<H', record, 18, 1)
    
    # First attribute offset
    struct.pack_into('<H', record, 20, 56)
    
    # Flags
    struct.pack_into('<H', record, 22, flags)
    
    # Used size and allocated size
    struct.pack_into('<I', record, 24, MFT_RECORD_SIZE)
    struct.pack_into('<I', record, 28, MFT_RECORD_SIZE)
    
    # File reference to base record
    struct.pack_into('<Q', record, 32, 0)
    
    # Next attribute ID
    struct.pack_into('<H', record, 40, 0)
    
    # Record number
    struct.pack_into('<I', record, 44, record_number)
    
    offset = 56
    
    # $STANDARD_INFORMATION attribute
    si_data = struct.pack('<QQQQLLLQQQ',
        windows_time(datetime.now()),  # Creation time
        windows_time(datetime.now() + timedelta(days=1)),  # Last modification time
        windows_time(datetime.now() + timedelta(days=2)),  # Last change time
        windows_time(datetime.now() + timedelta(days=3)),  # Last access time
        random.randint(0, 0xFFFFFFFF),  # File attributes
        0, 0, 0, 0, 0  # Other fields
    )
    offset = add_attribute(record, offset, STANDARD_INFORMATION_ATTRIBUTE, si_data)
    
    # $FILE_NAME attribute
    fn_data = struct.pack('<QQQQQQLLLLBB',
        5,  # Parent directory reference
        windows_time(datetime.now()),  # Creation time
        windows_time(datetime.now() + timedelta(days=1)),  # Last modification time
        windows_time(datetime.now() + timedelta(days=2)),  # Last change time
        windows_time(datetime.now() + timedelta(days=3)),  # Last access time
        1024,  # Allocated size
        1024,  # Real size
        flags,  # Flags
        0,  # Reparse value
        len(filename),  # Filename length
        0,  # Namespace
        0  
    ) + filename.encode('utf-16le')
    
    # $DATA attribute (resident)
    data = f"This is the content of {filename}".encode('utf-8')
    offset = add_attribute(record, offset, DATA_ATTRIBUTE, data)
    
    # $OBJECT_ID attribute
    obj_id_data = uuid.uuid4().bytes + uuid.uuid4().bytes + uuid.uuid4().bytes + uuid.uuid4().bytes
    offset = add_attribute(record, offset, OBJECT_ID_ATTRIBUTE, obj_id_data)
    
    # $SECURITY_DESCRIPTOR attribute
    sd_data = struct.pack('<BBHLLLL', 1, 0, 0x8004, 20, 40, 60, 80) + os.urandom(64)
    offset = add_attribute(record, offset, SECURITY_DESCRIPTOR_ATTRIBUTE, sd_data)
    
    # $VOLUME_NAME attribute (only for volume records)
    if record_number == 3:
        vn_data = "TestVolume".encode('utf-16le')
        offset = add_attribute(record, offset, VOLUME_NAME_ATTRIBUTE, vn_data)
    
    # $VOLUME_INFORMATION attribute (only for volume records)
    if record_number == 3:
        vi_data = struct.pack('<BBBBBBH', 0, 0, 0, 0, 3, 1, 0x0001)
        offset = add_attribute(record, offset, VOLUME_INFORMATION_ATTRIBUTE, vi_data)
    
    # $INDEX_ROOT attribute (for directories)
    if flags & FILE_RECORD_IS_DIRECTORY:
        ir_data = struct.pack('<LLLLBBHH', FILE_NAME_ATTRIBUTE, COLLATION_FILENAME, 4096, 1, 1, 0, 0, 0)
        offset = add_attribute(record, offset, INDEX_ROOT_ATTRIBUTE, ir_data)
    
    # $INDEX_ALLOCATION attribute (for directories)
    if flags & FILE_RECORD_IS_DIRECTORY:
        ia_data = struct.pack('<H', 16) + os.urandom(496)  # Simulating index records
        offset = add_attribute(record, offset, INDEX_ALLOCATION_ATTRIBUTE, ia_data)
    
    # $BITMAP attribute (for directories)
    if flags & FILE_RECORD_IS_DIRECTORY:
        bitmap_data = struct.pack('<L', 8) + b'\xff' * 8
        offset = add_attribute(record, offset, BITMAP_ATTRIBUTE, bitmap_data)
    
    # $REPARSE_POINT attribute (for some special files)
    if random.random() < 0.1:  # 10% chance
        rp_data = struct.pack('<LH', 0x80000000, 12) + b'\x00' * 2 + b"Reparse data"
        offset = add_attribute(record, offset, REPARSE_POINT_ATTRIBUTE, rp_data)
    
    # $EA_INFORMATION attribute
    eai_data = struct.pack('<LL', 256, 2)
    offset = add_attribute(record, offset, EA_INFORMATION_ATTRIBUTE, eai_data)
    
    # $EA attribute
    ea_data = struct.pack('<LBBH', 0, 0, 4, 5) + b"name" + b"value"
    offset = add_attribute(record, offset, EA_ATTRIBUTE, ea_data)
    
    # $LOGGED_UTILITY_STREAM attribute
    lus_data = struct.pack('<Q', 16) + b"Utility stream"
    offset = add_attribute(record, offset, LOGGED_UTILITY_STREAM_ATTRIBUTE, lus_data)
    
    return record

def add_attribute(record, offset, attr_type, data):
    attr_len = len(data) + 24  
    record[offset:offset+4] = struct.pack('<I', attr_type)
    record[offset+4:offset+8] = struct.pack('<I', attr_len)
    record[offset+8:offset+9] = b'\x00'  
    record[offset+9:offset+10] = b'\x00' 
    record[offset+10:offset+12] = struct.pack('<H', 24)
    record[offset+12:offset+14] = struct.pack('<H', 0) 
    record[offset+14:offset+16] = struct.pack('<H', 0) 
    record[offset+16:offset+20] = struct.pack('<L', len(data))  
    record[offset+20:offset+22] = struct.pack('<H', 0)  
    record[offset+24:offset+24+len(data)] = data
    return offset + attr_len

def create_sample_mft(filename, num_records=100):
    with open(filename, 'wb') as f:
        root_record = create_mft_record(5, FILE_RECORD_IN_USE | FILE_RECORD_IS_DIRECTORY, ".")
        f.write(root_record)
        
        volume_record = create_mft_record(3, FILE_RECORD_IN_USE, "$Volume")
        f.write(volume_record)
        
        for i in range(num_records - 2):  # -2 because we already created root and volume
            flags = random.choice([FILE_RECORD_IN_USE, FILE_RECORD_IN_USE | FILE_RECORD_IS_DIRECTORY])
            file_type = "DIR_" if flags & FILE_RECORD_IS_DIRECTORY else "FILE_"
             # Start from record 6 as the top 5 are generally MFT file specific and no use testing
            record = create_mft_record(i + 6, flags, f"{file_type}{i:04d}.txt") 
            f.write(record)

if __name__ == "__main__":
    create_sample_mft("sample_mft.bin", 100)
    print(f"Created sample MFT of size: {os.path.getsize('sample_mft.bin')} bytes")