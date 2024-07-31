import csv
import json
import os
import sys
from analyzemft import mft

def open_files(session):
    if session.options.version:
        print(f"Version is: {VERSION}")
        sys.exit()

    if session.options.filename is None:
        print("-f <filename> required.")
        sys.exit()

    try:
        session.file_mft = open(session.options.filename, 'rb')
    except IOError:
        print(f"Unable to open file: {session.options.filename}")
        sys.exit()

    if session.options.output is not None:
        try:
            session.file_csv = csv.writer(open(session.options.output, 'w'), dialect=csv.excel, quoting=1)
        except (IOError, TypeError):
            print(f"Unable to open file: {session.options.output}")
            sys.exit()
    
    if session.options.bodyfile is not None:
        try:
            session.file_body = open(session.options.bodyfile, 'w')
        except IOError:
            print(f"Unable to open file: {session.options.bodyfile}")
            sys.exit()

    if session.options.csvtimefile is not None:
        try:
            session.file_csv_time = open(session.options.csvtimefile, 'w')
        except (IOError, TypeError):
            print(f"Unable to open file: {session.options.csvtimefile}")
            sys.exit()

def process_mft_file(session):
    session.file_path_builder.build_filepaths()
    session.num_records = 0
    session.file_mft.seek(0)
    raw_record = session.file_mft.read(1024)

    if session.options.output is not None:
        session.file_csv.writerow(mft.mft_to_csv(None, True, session.options))

    while raw_record != b"":
        record = mft.parse_record(raw_record, session.options)
        if session.options.debug:
            print(record)

        record['filename'] = session.mft[session.num_records]['filename']
        do_output(session, record)

        session.num_records += 1

        if record['ads'] > 0:
            for i in range(record['ads']):
                record_ads = record.copy()
                record_ads['filename'] = record['filename'] + ':' + record['data_name', i].decode()
                do_output(session, record_ads)

        raw_record = session.file_mft.read(1024)

def do_output(session, record):
    if session.options.inmemory:
        session.fullmft[session.num_records] = record

    if session.options.output is not None:
        session.file_csv.writerow(mft.mft_to_csv(record, False, session.options))
    
    if session.options.json is not None:
        with open(session.options.json, 'a') as outfile:
            json.dump(mft.mft_to_json(record), outfile)
            outfile.write('\n')
    
    if session.options.csvtimefile is not None:
        session.file_csv_time.write(mft.mft_to_l2t(record))

    if session.options.bodyfile is not None:
        session.file_body.write(mft.mft_to_body(record, session.options.bodyfull, session.options.bodystd))

    if session.options.progress:
        if session.num_records % (session.mftsize // 5) == 0 and session.num_records > 0:
            print(f'Building MFT: {100.0 * session.num_records / session.mftsize:.0f}%')
