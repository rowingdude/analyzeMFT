"""
Test MFT file generator for analyzeMFT testing and validation
"""
import struct
import random
import os
import uuid
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple, Optional
from .constants import *

class MFTTestGenerator:
    """Generates test MFT files with various record types and scenarios"""
    
    def __init__(self):
        self.logger = logging.getLogger('analyzeMFT.test_generator')
        
    def windows_time(self, dt: datetime) -> int:
        """Convert a datetime object to Windows filetime"""
        # Windows epoch is January 1, 1601
        windows_epoch = datetime(1601, 1, 1)
        
        # Handle None datetime
        if dt is None:
            dt = datetime.now()
            
        # Calculate the difference
        delta = dt - windows_epoch
        
        # Convert to 100-nanosecond intervals
        return int(delta.total_seconds() * 10000000)
    
    def create_standard_info_attribute(self, 
                                     creation_time: Optional[datetime] = None,
                                     modification_time: Optional[datetime] = None,
                                     access_time: Optional[datetime] = None,
                                     entry_time: Optional[datetime] = None) -> bytes:
        """Create a STANDARD_INFORMATION attribute"""
        # Use current time as default
        now = datetime.now()
        
        creation_time = creation_time or now
        modification_time = modification_time or now
        access_time = access_time or now
        entry_time = entry_time or now
        
        # Standard Information structure (48 bytes)
        si_data = struct.pack('<QQQQI',
            self.windows_time(creation_time),     # Creation time
            self.windows_time(modification_time), # Modification time  
            self.windows_time(entry_time),        # MFT entry modification time
            self.windows_time(access_time),      # Access time
            
            # File attributes
            FILE_ATTRIBUTE_NORMAL if random.random() > 0.5 else FILE_ATTRIBUTE_HIDDEN
        )
        
        # Add padding to reach minimum 48 bytes
        si_data += b'\x00' * (48 - len(si_data))
        
        # Build complete attribute
        attr_header = struct.pack('<IBBHHHH',
            STANDARD_INFORMATION_ATTRIBUTE,  # Type
            len(si_data) + 24,              # Total length
            0,                              # Non-resident flag
            0,                              # Name length
            24,                             # Content offset
            0,                              # Compression flags
            0                               # Attribute ID
        )
        
        return attr_header + si_data
    
    def create_filename_attribute(self, filename: str, parent_ref: int = 5) -> bytes:
        """Create a FILE_NAME attribute"""
        # Convert filename to UTF-16LE
        filename_bytes = filename.encode('utf-16-le')
        filename_length = len(filename) 
        
        # Create times
        now = datetime.now()
        
        # File name structure - simplified
        file_size = random.randint(0, 1048576)
        fn_data = struct.pack('<Q',
            parent_ref,                           # Parent directory reference
        )
        fn_data += struct.pack('<QQQQ',
            self.windows_time(now),               # Creation time
            self.windows_time(now),               # Modification time
            self.windows_time(now),               # MFT modification time  
            self.windows_time(now),               # Access time
        )
        fn_data += struct.pack('<QQII',
            file_size,                           # Allocated size
            file_size,                           # Real size
            FILE_ATTRIBUTE_NORMAL,                # File attributes
            (filename_length << 8) | FILE_NAME_WIN32  # Combined length and namespace
        )
        fn_data += filename_bytes
        
        # Build complete attribute
        attr_header = struct.pack('<IBBHHHH',
            FILE_NAME_ATTRIBUTE,            # Type
            len(fn_data) + 24,             # Total length
            0,                             # Non-resident flag
            0,                             # Name length
            24,                            # Content offset
            0,                             # Compression flags
            0                              # Attribute ID
        )
        
        return attr_header + fn_data
    
    def create_data_attribute(self, size: int = 0) -> bytes:
        """Create a DATA attribute"""
        if size == 0:
            # Resident empty data attribute
            attr_header = struct.pack('<IBBHHHH',
                DATA_ATTRIBUTE,             # Type
                24,                        # Total length (header only)
                0,                         # Resident flag
                0,                         # Name length
                24,                        # Content offset
                0,                         # Compression flags
                0                          # Attribute ID
            )
            return attr_header
        else:
            # Non-resident data attribute
            attr_header = struct.pack('<IBBHHHH',
                DATA_ATTRIBUTE,             # Type
                64,                        # Total length
                1,                         # Non-resident flag
                0,                         # Name length
                64,                        # Content offset
                0,                         # Compression flags
                0                          # Attribute ID
            )
            
            # Non-resident info
            nr_data = struct.pack('<QQHHHH',
                0,                         # Starting VCN
                (size + 4095) // 4096 - 1, # Last VCN
                64,                        # Data runs offset
                0,                         # Compression unit size
                0,                         # Padding
                0                          # Reserved
            )
            nr_data += struct.pack('<QQQ',
                size,                      # Allocated size
                size,                      # Real size
                size                       # Initialized size
            )
            
            return attr_header + nr_data
    
    def create_mft_record(self, 
                         record_number: int,
                         is_directory: bool = False,
                         is_deleted: bool = False,
                         filename: str = None,
                         parent_ref: int = 5) -> bytes:
        """Create a complete MFT record"""
        record = bytearray(MFT_RECORD_SIZE)
        
        # FILE signature
        record[0:4] = MFT_RECORD_MAGIC
        
        # Update sequence offset and count
        struct.pack_into('<H', record, 4, 48)   # Update sequence offset
        struct.pack_into('<H', record, 6, 3)    # Update sequence count (1 + 2 for 1024 byte record)
        
        # Log file sequence number
        struct.pack_into('<Q', record, 8, random.randint(1, 1000000))
        
        # Sequence number
        struct.pack_into('<H', record, 16, random.randint(1, 100))
        
        # Link count
        struct.pack_into('<H', record, 18, 1 if not is_deleted else 0)
        
        # First attribute offset
        struct.pack_into('<H', record, 20, 56)
        
        # Flags
        flags = FILE_RECORD_IN_USE if not is_deleted else 0
        if is_directory:
            flags |= FILE_RECORD_IS_DIRECTORY
        struct.pack_into('<H', record, 22, flags)
        
        # Used size and allocated size
        struct.pack_into('<I', record, 24, MFT_RECORD_SIZE)
        struct.pack_into('<I', record, 28, MFT_RECORD_SIZE)
        
        # File reference to base record
        struct.pack_into('<Q', record, 32, 0)
        
        # Next attribute ID
        struct.pack_into('<H', record, 40, 4)
        
        # Record number (XP style)
        struct.pack_into('<I', record, 44, record_number)
        
        # Update sequence array
        record[48:50] = struct.pack('<H', 1)     # Update sequence number
        record[50:52] = struct.pack('<H', 0)     # First fixup value
        record[52:54] = struct.pack('<H', 0)     # Second fixup value
        
        # Add attributes
        offset = 56
        
        # Standard Information
        si_attr = self.create_standard_info_attribute()
        record[offset:offset+len(si_attr)] = si_attr
        offset += len(si_attr)
        
        # File Name
        if not filename:
            if is_directory:
                filename = f"TestDir_{record_number}"
            else:
                extensions = ['.txt', '.doc', '.exe', '.dll', '.log', '.dat']
                filename = f"TestFile_{record_number}{random.choice(extensions)}"
        
        fn_attr = self.create_filename_attribute(filename, parent_ref)
        record[offset:offset+len(fn_attr)] = fn_attr
        offset += len(fn_attr)
        
        # Data attribute (only for files)
        if not is_directory:
            data_size = random.choice([0, 512, 4096, 65536, 1048576])
            data_attr = self.create_data_attribute(data_size)
            record[offset:offset+len(data_attr)] = data_attr
            offset += len(data_attr)
        
        # End marker
        struct.pack_into('<I', record, offset, 0xFFFFFFFF)
        
        return bytes(record)
    
    def generate_test_mft(self, 
                         output_path: str,
                         num_records: int = 1000,
                         include_system_files: bool = True,
                         deletion_rate: float = 0.1,
                         directory_rate: float = 0.2) -> None:
        """Generate a test MFT file with specified characteristics"""
        output_path = Path(output_path)
        self.logger.warning(f"Generating test MFT file: {output_path}")
        self.logger.warning(f"Parameters: {num_records} records, {deletion_rate:.0%} deleted, {directory_rate:.0%} directories")
        
        with open(output_path, 'wb') as f:
            # System files (first 16 records)
            if include_system_files:
                system_files = [
                    "$MFT", "$MFTMirr", "$LogFile", "$Volume", "$AttrDef",
                    ".", "$Bitmap", "$Boot", "$BadClus", "$Secure",
                    "$UpCase", "$Extend", None, None, None, None
                ]
                
                for i in range(16):
                    if system_files[i]:
                        record = self.create_mft_record(
                            i, 
                            is_directory=(i == 5),  # Root directory
                            is_deleted=False,
                            filename=system_files[i],
                            parent_ref=5 if i != 5 else 5
                        )
                    else:
                        # Empty record
                        record = b'\x00' * MFT_RECORD_SIZE
                    f.write(record)
                
                start_record = 16
            else:
                start_record = 0
            
            # Regular files and directories
            directories = [5]  # Start with root directory
            
            for i in range(start_record, num_records):
                is_directory = random.random() < directory_rate
                is_deleted = random.random() < deletion_rate
                
                # Choose parent directory
                parent_ref = random.choice(directories) if directories else 5
                
                record = self.create_mft_record(
                    i,
                    is_directory=is_directory,
                    is_deleted=is_deleted,
                    parent_ref=parent_ref
                )
                
                if is_directory and not is_deleted:
                    directories.append(i)
                
                f.write(record)
                
                # Progress indicator
                if (i + 1) % 100 == 0:
                    self.logger.info(f"Generated {i + 1}/{num_records} records...")
        
        self.logger.warning(f"Test MFT file generated successfully: {output_path}")
        self.logger.warning(f"File size: {output_path.stat().st_size:,} bytes")
    
    def generate_anomaly_mft(self, output_path: str) -> None:
        """Generate an MFT file with various anomalies for testing"""
        output_path = Path(output_path)
        self.logger.warning(f"Generating anomaly test MFT file: {output_path}")
        
        with open(output_path, 'wb') as f:
            # Normal system files first
            for i in range(5):
                record = self.create_mft_record(i, is_directory=(i == 5))
                f.write(record)
            
            # Root directory
            record = self.create_mft_record(5, is_directory=True, filename=".")
            f.write(record)
            
            # Anomaly 1: Orphaned file (parent doesn't exist)
            record = self.create_mft_record(6, filename="Orphaned.txt", parent_ref=9999)
            f.write(record)
            
            # Anomaly 2: Self-referential file
            record = self.create_mft_record(7, filename="SelfRef.txt", parent_ref=7)
            f.write(record)
            
            # Anomaly 3: Future timestamps
            future_record = bytearray(self.create_mft_record(8, filename="Future.txt"))
            # Modify the SI timestamp to be in the future
            future_time = self.windows_time(datetime.now() + timedelta(days=365))
            struct.pack_into('<Q', future_record, 56 + 24, future_time)
            f.write(bytes(future_record))
            
            # Anomaly 4: Very old timestamps
            old_record = bytearray(self.create_mft_record(9, filename="Ancient.txt"))
            # Modify the SI timestamp to be very old
            old_time = self.windows_time(datetime(1980, 1, 1))
            struct.pack_into('<Q', old_record, 56 + 24, old_time)
            f.write(bytes(old_record))
            
            # Anomaly 5: Mismatched timestamps (SI vs FN)
            # This is handled by the regular generator as times differ slightly
            
            # Anomaly 6: Invalid magic number
            bad_magic = bytearray(self.create_mft_record(10, filename="BadMagic.txt"))
            bad_magic[0:4] = b'BADF'
            f.write(bytes(bad_magic))
            
            # Anomaly 7: Zero-length filename
            zero_fn = bytearray(self.create_mft_record(11))
            # Find FILE_NAME attribute and set length to 0
            # This is complex, so we'll skip for now
            f.write(bytes(zero_fn))
            
            # Fill remaining records normally
            for i in range(12, 100):
                record = self.create_mft_record(
                    i,
                    is_directory=(random.random() < 0.2),
                    is_deleted=(random.random() < 0.1)
                )
                f.write(record)
        
        self.logger.warning(f"Anomaly test MFT file generated: {output_path}")

def create_test_mft(output_path: str = "test.mft", 
                   num_records: int = 1000,
                   test_type: str = "normal") -> None:
    """Convenience function to create test MFT files"""
    generator = MFTTestGenerator()
    
    if test_type == "anomaly":
        generator.generate_anomaly_mft(output_path)
    else:
        generator.generate_test_mft(
            output_path,
            num_records=num_records,
            include_system_files=True,
            deletion_rate=0.1,
            directory_rate=0.2
        )