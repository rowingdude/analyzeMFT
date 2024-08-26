import aiofiles
import sys
from pathlib import Path
from typing import Optional, BinaryIO, TextIO
from dataclasses import dataclass

@dataclass
class FileHandlerOptions:
    filename: Path
    output: Optional[Path] = None
    bodyfile: Optional[Path] = None
    csvtimefile: Optional[Path] = None

class FileOpenError(Exception):
    pass

class FileHandler:
    def __init__(self, options: FileHandlerOptions):
        self.options = options
        self.file_mft: Optional[BinaryIO] = None
        self.file_csv: Optional[TextIO] = None
        self.file_body: Optional[TextIO] = None
        self.file_csv_time: Optional[TextIO] = None

    async def __aenter__(self):
        await self.open_files()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_files()

    async def open_files(self):
        try:
            print(f"Opening MFT file: {self.options.filename}")
            self.file_mft = await aiofiles.open(self.options.filename, 'rb')
            print("MFT file opened successfully")
            
            if self.options.output:
                print(f"Opening CSV output file: {self.options.output}")
                self.file_csv = await aiofiles.open(self.options.output, 'w', newline='', encoding='utf-8')
                print("CSV output file opened successfully")
            
            # Leaving the rest alone until CSV works correctly           
            if self.options.bodyfile:
                self.file_body = await aiofiles.open(self.options.bodyfile, 'w', encoding='utf-8')
            
            if self.options.csvtimefile:
                self.file_csv_time = await aiofiles.open(self.options.csvtimefile, 'w', encoding='utf-8')
            
            if not self.file_mft:
                raise FileOpenError("MFT file not opened successfully.")
        
        except Exception as e:
            print(f"Error opening files: {str(e)}")
            traceback.print_exc()
            sys.exit(1)

    async def close_files(self):
        files_to_close = [self.file_mft, self.file_csv, self.file_body, self.file_csv_time]
        for file in files_to_close:
            if file:
                await file.close()
                
    async def read_mft_record(self) -> Optional[bytes]:
        if not self.file_mft:
            raise FileOpenError("MFT file is not open.")
        try:
            raw_record = await self.file_mft.read(1024)  # Assuming each record is 1024 bytes
            if not raw_record:
                return None  # End of file
            if len(raw_record) < 1024:
                print(f"Warning: Incomplete record read. Expected 1024 bytes, got {len(raw_record)}")
            return raw_record
        except Exception as e:
            print(f"Error reading MFT record: {str(e)}")
            traceback.print_exc()
            return None

    async def estimate_total_records(self) -> int:
        if not self.file_mft:
            raise FileOpenError("MFT file is not open.")
        current_position = await self.file_mft.tell()
        await self.file_mft.seek(0, 2) 
        file_size = await self.file_mft.tell()
        await self.file_mft.seek(current_position) 
        return file_size // 1024  

    async def write_csv(self, data: str):
        if not self.file_csv:
            raise FileOpenError("CSV file is not open.")
        print(f"Writing {len(data)} bytes to CSV file")
        await self.file_csv.write(data)
        await self.file_csv.flush()
        print("Finished writing to CSV file")

    async def write_bodyfile(self, data: str):
        if not self.file_body:
            raise FileOpenError("Body file is not open.")
        await self.file_body.write(data)
        await self.file_body.flush()

    async def write_csvtime(self, data: str):
        if not self.file_csv_time:
            raise FileOpenError("CSV time file is not open.")
        await self.file_csv_time.write(data)
        await self.file_csv_time.flush()