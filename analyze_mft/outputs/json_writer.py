import json
from typing import Dict, Any

class JSONWriter:
    def __init__(self, options: Any, file_handler: Any):
        self.options = options
        self.file_handler = file_handler
        self.json_data = []

    async def write_json_record(self, record: Dict[str, Any]):
        self.json_data.append(record)

    async def write_json_file(self):
        if self.options.jsonfile:
            json_string = json.dumps(self.json_data, indent=4)
            await self.file_handler.write_json(json_string)