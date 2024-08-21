from .common_imports import *

class FileHandler:
    def __init__(self, options):
        self.options = options
        self.file_mft = None
        self.file_csv = None
        self.file_body = None
        self.file_csv_time = None

    def open_files(self):
        try:
            self.file_mft = open(self.options.filename, 'rb')
        except:
            print(f"Unable to open file: {self.options.filename}")
            sys.exit()

        if self.options.output is not None:
            try:
                self.file_csv = open(self.options.output, 'w', newline='', encoding='utf-8')
            except:
                print(f"Unable to open file: {self.options.output}")
                sys.exit()

        if self.options.bodyfile is not None:
            try:
                self.file_body = open(self.options.bodyfile, 'w', encoding='utf-8')
            except:
                print(f"Unable to open file: {self.options.bodyfile}")
                sys.exit()

        if self.options.csvtimefile is not None:
            try:
                self.file_csv_time = open(self.options.csvtimefile, 'w', encoding='utf-8')
            except:
                print(f"Unable to open file: {self.options.csvtimefile}")
                sys.exit()

    def read_mft_record(self):
        return self.file_mft.read(1024)