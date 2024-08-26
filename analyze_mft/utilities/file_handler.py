import aiofiles
from typing import Optional, BinaryIO, TextIO
from dataclasses import dataclass

@dataclass
class FileHandlerOptions:
    filename: str
    output: Optional[str] = None
    bodyfile: Optional[str] = None
    csvtimefile: Optional[str] = None

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
        self.file_mft = await aiofiles.open(self.options.filename, 'rb')
        if self.options.output:
            self.file_csv = await aiofiles.open(self.options.output, 'w', newline='')
        if self.options.bodyfile:
            self.file_body = await aiofiles.open(self.options.bodyfile, 'w')
        if self.options.csvtimefile:
            self.file_csv_time = await aiofiles.open(self.options.csvtimefile, 'w')

    async def close_files(self):
        files_to_close = [self.file_mft, self.file_csv, self.file_body, self.file_csv_time]
        for file in files_to_close:
            if file:
                await file.close()

    async def read_mft_record(self) -> Optional[bytes]:
        return await self.file_mft.read(1024)  # Assuming each record is 1024 bytes

    async def write_csv(self, data: str):
        if self.file_csv:
            await self.file_csv.write(data)

    async def write_body(self, data: str):
        if self.file_body:
            await self.file_body.write(data)

    async def write_csv_time(self, data: str):
        if self.file_csv_time:
            await self.file_csv_time.write(data)