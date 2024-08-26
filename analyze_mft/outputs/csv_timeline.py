class CSVTimelineWriter:
    def __init__(self, options, file_handler):
        self.options = options
        self.file_handler = file_handler

    async def write_records(self, mft):
        for record in mft.values():
            csv_timeline_record = self._prepare_csv_timeline_record(record)
            await self.file_handler.write_csvtime(csv_timeline_record)

    def _prepare_csv_timeline_record(self, record):
        
        pass