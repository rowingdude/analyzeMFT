import asyncio
import csv
import os
import json
import sqlite3
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from .mft_record import MftRecord
from .constants import *

class FileWriters:
    @staticmethod
    async def write_csv(records: List[MftRecord], output_file: str) -> None:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(CSV_HEADER) 
            for record in records:
                writer.writerow(record.to_csv())
            await asyncio.sleep(0)  

    @staticmethod
    async def write_json(records: List[MftRecord], output_file: str) -> None:
        json_data = [record.__dict__ for record in records]
        with open(output_file, 'w', encoding='utf-8') as jsonfile:
            json.dump(json_data, jsonfile, indent=2, default=str)
        await asyncio.sleep(0)

    @staticmethod
    async def write_xml(records: List[MftRecord], output_file: str) -> None:
        root = ET.Element("mft_records")
        for record in records:
            record_elem = ET.SubElement(root, "record")
            for key, value in record.__dict__.items():
                ET.SubElement(record_elem, key).text = str(value)
        tree = ET.ElementTree(root)
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        await asyncio.sleep(0)

    @staticmethod
    async def write_excel(records: List[MftRecord], output_file: str) -> None:
        try:
            import openpyxl
        except ImportError:
            print("openpyxl is not installed. Please install it to use Excel export.")
            return

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(CSV_HEADER) 
        for record in records:
            ws.append(record.to_csv())
        wb.save(output_file)
        await asyncio.sleep(0)

    @staticmethod
    async def write_body(records: List[MftRecord], output_file: str) -> None:
        with open(output_file, 'w', encoding='utf-8') as bodyfile:
            for record in records:
                # Format: MD5|name|inode|mode_as_string|UID|GID|size|atime|mtime|ctime|crtime
                bodyfile.write(f"0|{record.filename}|{record.recordnum}|{record.flags:04o}|0|0|"
                               f"{record.filesize}|{record.fn_times['atime'].unixtime}|"
                               f"{record.fn_times['mtime'].unixtime}|{record.fn_times['ctime'].unixtime}|"
                               f"{record.fn_times['crtime'].unixtime}\n")
            await asyncio.sleep(0)

    @staticmethod
    async def write_timeline(records: List[MftRecord], output_file: str) -> None:
        with open(output_file, 'w', encoding='utf-8') as timeline:
            for record in records:
                # Format: Time|Source|Type|User|Host|Short|Desc|Version|Filename|Inode|Notes|Format|Extra
                timeline.write(f"{record.fn_times['crtime'].unixtime}|MFT|CREATE|||||{record.filename}|{record.recordnum}||||\n")
                timeline.write(f"{record.fn_times['mtime'].unixtime}|MFT|MODIFY|||||{record.filename}|{record.recordnum}||||\n")
                timeline.write(f"{record.fn_times['atime'].unixtime}|MFT|ACCESS|||||{record.filename}|{record.recordnum}||||\n")
                timeline.write(f"{record.fn_times['ctime'].unixtime}|MFT|CHANGE|||||{record.filename}|{record.recordnum}||||\n")
            await asyncio.sleep(0)

    @staticmethod
    async def write_l2t(records: List[MftRecord], output_file: str) -> None:
        with open(output_file, 'w', newline='', encoding='utf-8') as l2tfile:
            writer = csv.writer(l2tfile)
            writer.writerow(['date', 'time', 'timezone', 'MACB', 'source', 'sourcetype', 'type', 'user', 'host', 'short', 'desc', 'version', 'filename', 'inode', 'notes', 'format', 'extra'])
            for record in records:
                for time_type, time_obj in record.fn_times.items():
                    macb = 'M' if time_type == 'mtime' else 'A' if time_type == 'atime' else 'C' if time_type == 'ctime' else 'B'
                    date_str = time_obj.dt.strftime('%m/%d/%Y') if time_obj.dt else ''
                    time_str = time_obj.dt.strftime('%H:%M:%S') if time_obj.dt else ''
                    writer.writerow([
                        date_str, time_str, 'UTC', macb, 'MFT', 'FILESYSTEM', time_type, '', '', '',
                        f"{record.filename} {time_type}", '', record.filename, record.recordnum, '', '', ''
                    ])
            await asyncio.sleep(0)


    @staticmethod
    async def write_sqlite(records: List[MftRecord], output_file: str) -> None:
        conn = sqlite3.connect(output_file)
        cursor = conn.cursor()

        # Create and populate static tables
        sql_dir = os.path.join(os.path.dirname(__file__), 'sql')
        for sql_file in os.listdir(sql_dir):
            with open(os.path.join(sql_dir, sql_file), 'r') as f:
                cursor.executescript(f.read())

        # Create MFT records table
        cursor.execute('''
            CREATE TABLE mft_records (
                record_number INTEGER PRIMARY KEY,
                filename TEXT,
                parent_record_number INTEGER,
                file_size INTEGER,
                is_directory INTEGER,
                creation_time TEXT,
                modification_time TEXT,
                access_time TEXT,
                entry_time TEXT,
                attribute_types TEXT
            )
        ''')

        # Insert MFT records
        for record in records:
            cursor.execute('''
                INSERT INTO mft_records (
                    record_number, filename, parent_record_number, file_size,
                    is_directory, creation_time, modification_time, access_time,
                    entry_time, attribute_types
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.recordnum,
                record.filename,
                record.get_parent_record_num(),
                record.filesize,
                1 if record.flags & FILE_RECORD_IS_DIRECTORY else 0,
                record.fn_times['crtime'].dtstr,
                record.fn_times['mtime'].dtstr,
                record.fn_times['atime'].dtstr,
                record.fn_times['ctime'].dtstr,
                ','.join(map(str, record.attribute_types))
            ))

        conn.commit()
        conn.close()
        await asyncio.sleep(0)

    @staticmethod
    async def write_tsk(records: List[MftRecord], output_file: str) -> None:
        with open(output_file, 'w', newline='', encoding='utf-8') as tskfile:
            for record in records:
                # TSK body file format:
                # MD5|name|inode|mode_as_string|UID|GID|size|atime|mtime|ctime|crtime
                tskfile.write(f"0|{record.filename}|{record.recordnum}|{record.flags:04o}|0|0|"
                              f"{record.filesize}|{record.fn_times['atime'].unixtime}|"
                              f"{record.fn_times['mtime'].unixtime}|{record.fn_times['ctime'].unixtime}|"
                              f"{record.fn_times['crtime'].unixtime}\n")
            await asyncio.sleep(0)