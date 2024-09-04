import csv
import json
import xml.etree.ElementTree as ET
import asyncio
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