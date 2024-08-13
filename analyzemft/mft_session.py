#!/usr/bin/env python

# Version 2.1.1
#
# Author: Benjamin Cance (bjc@tdx.li)
# Copyright Benjamin Cance 2024

VERSION='2.1.1'

import json
import logging
from pathlib import Path
from typing import TextIO
from .mft_analyzer import MFTAnalyzer
from .mft_formatters import mft_to_csv, mft_to_body, mft_to_l2t, mft_to_json


class MftSession:
    def __init__(self):
        self.mft = {}
        self.folders = {}
        self.options = None
        self.file_mft: TextIO = None
        self.file_csv = None
        self.file_body: TextIO = None
        self.file_csv_time: TextIO = None
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def open_files(self):
        try:
            self.file_mft = open(self.options.filename, 'rb')
        except IOError as e:
            logging.error(f"Unable to open file: {self.options.filename}. Error: {e}")
            sys.exit(1)

        if self.options.output:
            try:
                output_file = open(self.options.output, 'w', newline='')
                self.file_csv = csv.writer(output_file, dialect=csv.excel, quoting=csv.QUOTE_ALL)
            except IOError as e:
                logging.error(f"Unable to open file: {self.options.output}. Error: {e}")
                sys.exit(1)

        if self.options.bodyfile:
            try:
                self.file_body = open(self.options.bodyfile, 'w')
            except IOError as e:
                logging.error(f"Unable to open file: {self.options.bodyfile}. Error: {e}")
                sys.exit(1)

        if self.options.csvtimefile:
            try:
                self.file_csv_time = open(self.options.csvtimefile, 'w')
            except IOError as e:
                logging.error(f"Unable to open file: {self.options.csvtimefile}. Error: {e}")
                sys.exit(1)

    def process_mft_file(self):
        analyzer = MFTAnalyzer(self.options)
        analyzer.process_mft_file(self.file_mft)
        self.mft = analyzer.mft
        self.folders = analyzer.folders

    def print_records(self):
        for i, record in self.mft.items():
            if self.file_csv:
                self.file_csv.writerow(mft_to_csv(record, False))
            if self.file_csv_time:
                self.file_csv_time.write(mft_to_l2t(record))
            if self.file_body:
                self.file_body.write(mft_to_body(record, self.options.bodyfull, self.options.bodystd))
            if self.options.json:
                print(mft_to_json(record)) 

    def close_files(self):
        for file in [self.file_mft, self.file_body, self.file_csv_time]:
            if file:
                file.close()
        if self.file_csv:
            self.file_csv.close()

    def run(self):
        try:
            self.open_files()
            self.process_mft_file()
            self.print_records()
        finally:
            self.close_files()
