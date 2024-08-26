from typing import Dict, Any, List
from io import StringIO
import csv
from analyze_mft.utilities.logger import Logger

class CSVTimelineWriter:
    def __init__(self, options: Any, file_handler: Any, logger: Logger):
        self.options = options
        self.file_handler = file_handler
        self.logger = logger

    async def write_records(self, mft: Dict[int, Dict[str, Any]]):
        for record in mft.values():
            csv_timeline_record = await self._prepare_csv_timeline_record(record)
            output = StringIO()
            csv.writer(output).writerow(csv_timeline_record)
            await self.file_handler.write_csv_time(output.getvalue())

    async def _prepare_csv_timeline_record(self, record: Dict[str, Any]) -> List[str]:
        timeline_record = [
            record.get('filename', ''),
            str(record.get('recordnum', '')),
            record.get('si', {}).get('crtime', ''),
            record.get('si', {}).get('mtime', ''),
            record.get('si', {}).get('atime', ''),
            record.get('si', {}).get('ctime', ''),
            record.get('fn', {}).get('crtime', ''),
            record.get('fn', {}).get('mtime', ''),
            record.get('fn', {}).get('atime', ''),
            record.get('fn', {}).get('ctime', '')
        ]
        return timeline_record