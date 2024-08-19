from .common_imports import *

class JSONWriter:
    def __init__(self, options, file_handler):
        self.options = options
        self.file_handler = file_handler
        self.json_data = []

    def write_json_record(self, record):
        self.json_data.append(record)

    def write_json_file(self):
        if self.options.jsonfile:
            with open(self.options.jsonfile, 'w', encoding='utf-8') as json_file:
                json.dump(self.json_data, json_file, indent=4)