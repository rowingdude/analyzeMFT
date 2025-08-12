
import struct
import random
import os
import uuid
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple, Optional
from .constants import *

logger = logging.getLogger('analyzeMFT.test_generator')

class MFTTestGenerator:
    
    def __init__(self):
        self.logger = logging.getLogger('analyzeMFT.test_generator')
        self.windows_epoch = datetime(1601, 1, 1)
    
    def windows_time(self, dt: datetime) -> int:

        delta = dt - self.windows_epoch
        return int(delta.total_seconds() * 10000000)
    
    def create_standard_info_attribute(self, 
                                     creation_time: Optional[datetime] = None,
                                     modification_time: Optional[datetime] = None,
                                     access_time: Optional[datetime] = None,
                                     entry_time: Optional[datetime] = None) -> bytes:

        now = datetime.now()
        creation_time = creation_time or now
        modification_time = modification_time or now
        access_time = access_time or now
        entry_time = entry_time or now
        
        si_data = struct.pack('<QQQQI',
            self.windows_time(creation_time),
            self.windows_time(modification_time),
            self.windows_time(entry_time),
            self.windows_time(access_time),
            FILE_ATTRIBUTE_NORMAL if random.random() > 0.5 else FILE_ATTRIBUTE_HIDDEN
        )
        
        si_data += b'\x00' * (48 - len(si_data))
        
        attr_header = struct.pack('<IBBHHHH',
            STANDARD_INFORMATION_ATTRIBUTE,
            len(si_data) + 24,  
            0,  
            0,  
            24,  
            0,  
            0   
        )
        
        return attr_header + si_data
    
    def create_filename_attribute(self, filename: str, parent_ref: int = 5) -> bytes:

        filename_bytes = filename.encode('utf-16le')
        filename_length = len(filename)
        now = datetime.now()
        file_size = random.randint(0, 1048576)
        
        
        fn_data = struct.pack('<Q', parent_ref)
        fn_data += struct.pack('<QQQQ',
            self.windows_time(now),
            self.windows_time(now),
            self.windows_time(now),
            self.windows_time(now),
        )
        fn_data += struct.pack('<QQII',
            file_size,
            file_size,
            FILE_ATTRIBUTE_NORMAL,
            (filename_length << 8) | FILE_NAME_WIN32
        )
        fn_data += filename_bytes
        
        
        attr_header = struct.pack('<IBBHHHH',
            FILE_NAME_ATTRIBUTE,
            len(fn_data) + 24,  
            0,  
            0,  
            24,  
            0,  
            0   
        )
        
        return attr_header + fn_data
    
    def create_data_attribute(self, size: int = 0) -> bytes:
        """
        Create a data attribute.
        
        Args:
            size: Size of the data attribute
            
        Returns:
            Data attribute bytes
        """
        if size == 0:
            
            attr_header = struct.pack('<IBBHHHH',
                DATA_ATTRIBUTE,
                24,  
                0,   
                0,   
                24,  
                0,   
                0    
            )
            return attr_header
        else:
            
            attr_header = struct.pack('<IBBHHHH',
                DATA_ATTRIBUTE,
                64,  
                1,   
                0,   
                64,  
                0,   
                0    
            )
            
            nr_data = struct.pack('<QQHHHH',
                0,                    
                (size + 4095) // 4096 - 1,  
                64,                   
                0,                    
                0,                    
                0                     
            )
            nr_data += struct.pack('<QQQ',
                size,   
                size,   
                size    
            )
            
            return attr_header + nr_data
    
    def create_mft_record(self, 
                         record_number: int,
                         is_directory: bool = False,
                         is_deleted: bool = False,
                         filename: Optional[str] = None,
                         parent_ref: int = 5) -> bytes:

        record = bytearray(MFT_RECORD_SIZE)
        
        record[0:4] = MFT_RECORD_MAGIC
        struct.pack_into('<H', record, 4, 48)  
        struct.pack_into('<H', record, 6, 3)   
        struct.pack_into('<Q', record, 8, random.randint(1, 1000000))  
        struct.pack_into('<H', record, 16, random.randint(1, 100))     
        struct.pack_into('<H', record, 18, 1 if not is_deleted else 0) 
        struct.pack_into('<H', record, 20, 56)  
        flags = FILE_RECORD_IN_USE if not is_deleted else 0
        if is_directory:
            flags |= FILE_RECORD_IS_DIRECTORY
        struct.pack_into('<H', record, 22, flags)  
        struct.pack_into('<I', record, 24, MFT_RECORD_SIZE)  
        struct.pack_into('<I', record, 28, MFT_RECORD_SIZE)  
        struct.pack_into('<Q', record, 32, 0)     
        struct.pack_into('<H', record, 40, 4)     
        struct.pack_into('<I', record, 44, record_number)  
        
        record[48:50] = struct.pack('<H', 1)
        record[50:52] = struct.pack('<H', 0)
        record[52:54] = struct.pack('<H', 0)
        
        offset = 56
        
        si_attr = self.create_standard_info_attribute()
        record[offset:offset+len(si_attr)] = si_attr
        offset += len(si_attr)
        
        if not filename:
            if is_directory:
                filename = f"TestDir_{record_number}"
            else:
                extensions = ['.txt', '.doc', '.exe', '.dll', '.log', '.dat']
                filename = f"TestFile_{record_number}{random.choice(extensions)}"
        
        fn_attr = self.create_filename_attribute(filename, parent_ref)
        record[offset:offset+len(fn_attr)] = fn_attr
        offset += len(fn_attr)
        
        if not is_directory:
            data_size = random.choice([0, 512, 4096, 65536, 1048576])
            data_attr = self.create_data_attribute(data_size)
            record[offset:offset+len(data_attr)] = data_attr
            offset += len(data_attr)
        
        struct.pack_into('<I', record, offset, 0xFFFFFFFF)
        
        return bytes(record)
    
    def generate_test_mft(self, 
                         output_path: str,
                         num_records: int = 1000,
                         include_system_files: bool = True,
                         deletion_rate: float = 0.1,
                         directory_rate: float = 0.2) -> None:
        output_path = Path(output_path)
        self.logger.warning(f"Generating test MFT file: {output_path}")
        self.logger.warning(f"Parameters: {num_records} records, {deletion_rate:.0%} deleted, {directory_rate:.0%} directories")
        
        with open(output_path, 'wb') as f:
            directories = [5]  
            
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
                            is_directory=(i == 5),
                            is_deleted=False,
                            filename=system_files[i],
                            parent_ref=5 if i != 5 else 5
                        )
                    else:
                        record = b'\x00' * MFT_RECORD_SIZE
                    f.write(record)
                
                start_record = 16
                directories.extend(range(16))  
            else:
                start_record = 0
            
            for i in range(start_record, num_records):
                is_directory = random.random() < directory_rate
                is_deleted = random.random() < deletion_rate
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
                
                if (i + 1) % 100 == 0:
                    self.logger.info(f"Generated {i + 1}/{num_records} records...")
        
        file_size = output_path.stat().st_size
        self.logger.warning(f"Test MFT file generated successfully: {output_path}")
        self.logger.warning(f"File size: {file_size:,} bytes")
    
    def generate_anomaly_mft(self, output_path: str) -> None:

        output_path = Path(output_path)
        self.logger.warning(f"Generating anomaly test MFT file: {output_path}")
        
        with open(output_path, 'wb') as f:
            
            for i in range(5):
                record = self.create_mft_record(i, is_directory=(i == 5))
                f.write(record)
            
            record = self.create_mft_record(5, is_directory=True, filename=".")
            f.write(record)
            
            record = self.create_mft_record(6, filename="Orphaned.txt", parent_ref=9999)
            f.write(record)
            
            record = self.create_mft_record(7, filename="SelfRef.txt", parent_ref=7)
            f.write(record)
            
            future_record = bytearray(self.create_mft_record(8, filename="Future.txt"))
            future_time = self.windows_time(datetime.now() + timedelta(days=365))
            struct.pack_into('<Q', future_record, 56 + 24, future_time)  
            f.write(bytes(future_record))
            
            old_record = bytearray(self.create_mft_record(9, filename="Ancient.txt"))
            old_time = self.windows_time(datetime(1980, 1, 1))
            struct.pack_into('<Q', old_record, 56 + 24, old_time)  
            f.write(bytes(old_record))
            
            bad_magic = bytearray(self.create_mft_record(10, filename="BadMagic.txt"))
            bad_magic[0:4] = b'BADF'
            f.write(bytes(bad_magic))
            
            zero_fn = bytearray(self.create_mft_record(11))
            f.write(bytes(zero_fn))
            
            for i in range(12, 100):
                record = self.create_mft_record(
                    i,
                    is_directory=(random.random() < 0.2),
                    is_deleted=(random.random() < 0.1)
                )
                f.write(record)
        
        file_size = output_path.stat().st_size
        self.logger.warning(f"Anomaly test MFT file generated: {output_path}")
        self.logger.warning(f"File size: {file_size:,} bytes")


def create_test_mft(output_path: str = "test.mft", 
                   num_records: int = 1000,
                   test_type: str = "normal") -> None:

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