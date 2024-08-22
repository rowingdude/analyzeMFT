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
        
        except IOError as e:
            
            print(f"Error: Unable to open MFT file: {self.options.filename}. {e}")
            sys.exit(1)

        if self.options.output is not None:

            try:
            
                self.file_csv = open(self.options.output, 'w', newline='', encoding='utf-8')
            
            except IOError as e:
            
                print(f"Error: Unable to open output CSV file: {self.options.output}. {e}")
                sys.exit(1)

        if self.options.bodyfile is not None:
            
            try:
            
                self.file_body = open(self.options.bodyfile, 'w', encoding='utf-8')
            
            except IOError as e:
            
                print(f"Error: Unable to open bodyfile: {self.options.bodyfile}. {e}")
                sys.exit(1)

        if self.options.csvtimefile is not None:
            
            try:
            
                self.file_csv_time = open(self.options.csvtimefile, 'w', encoding='utf-8')
            
            except IOError as e:
            
                print(f"Error: Unable to open CSV time file: {self.options.csvtimefile}. {e}")
                sys.exit(1)

        if not self.file_mft:
            
            print("Error: MFT file not opened successfully.")
            sys.exit(1)

    def read_mft_record(self):
        
        raw_record = self.file_mft.read(1024) 
        if not raw_record:
            return None
        return raw_record