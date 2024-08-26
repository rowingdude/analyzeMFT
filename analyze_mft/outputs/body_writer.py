class BodyFileWriter:
    def __init__(self, options, file_handler):
        self.options = options
        self.file_handler = file_handler

    async def write_records(self, mft):
        for record in mft.values():
            body_record = self._prepare_body_record(record)
            await self.file_handler.write_bodyfile(body_record)

    def _prepare_body_record(self, record):
       
        pass