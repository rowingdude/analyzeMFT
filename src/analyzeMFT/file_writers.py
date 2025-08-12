import asyncio
import csv
import logging
import os
import json
import sqlite3
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from .mft_record import MftRecord
from .constants import *

logger = logging.getLogger('analyzeMFT.writers')

class FileWriters:
    
    @staticmethod
    async def write_csv(records: List[MftRecord], output_file: str) -> None:
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(CSV_HEADER)
                for record in records:
                    writer.writerow(record.to_csv())
        except Exception as e:
            logger.error(f"Error writing CSV file {output_file}: {e}")
            raise

    @staticmethod
    async def write_json(records: List[MftRecord], output_file: str) -> None:
        try:
            json_data = [record.__dict__ for record in records]
            with open(output_file, 'w', encoding='utf-8') as jsonfile:
                json.dump(json_data, jsonfile, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error writing JSON file {output_file}: {e}")
            raise

    @staticmethod
    async def write_xml(records: List[MftRecord], output_file: str) -> None:
        try:
            root = ET.Element("mft_records")
            for record in records:
                record_elem = ET.SubElement(root, "record")
                for key, value in record.__dict__.items():
                    elem = ET.SubElement(record_elem, key)
                    elem.text = str(value) if value is not None else ""
            
            tree = ET.ElementTree(root)
            tree.write(output_file, encoding='utf-8', xml_declaration=True)
        except Exception as e:
            logger.error(f"Error writing XML file {output_file}: {e}")
            raise

    @staticmethod
    async def write_excel(records: List[MftRecord], output_file: str) -> None:
        try:
            import openpyxl
        except ImportError:
            logger.error("openpyxl is not installed. Please install it to use Excel export: pip install openpyxl")
            raise ImportError("openpyxl is required for Excel export")
        
        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "MFT Records"
            ws.append(CSV_HEADER)
            
            for record in records:
                try:
                    ws.append(record.to_csv())
                except Exception as e:
                    logger.warning(f"Error writing record {record.recordnum} to Excel: {e}")
                    # Write empty row or skip
                    ws.append([""] * len(CSV_HEADER))
            
            wb.save(output_file)
        except Exception as e:
            logger.error(f"Error writing Excel file {output_file}: {e}")
            raise

    @staticmethod
    async def write_body(records: List[MftRecord], output_file: str) -> None:
        try:
            with open(output_file, 'w', encoding='utf-8') as bodyfile:
                for record in records:
                    try:
                        # Format: MD5|name|inode|mode_as_string|UID|GID|size|atime|mtime|ctime|crtime
                        atime = getattr(record.fn_times.get('atime'), 'unixtime', 0) or 0
                        mtime = getattr(record.fn_times.get('mtime'), 'unixtime', 0) or 0
                        ctime = getattr(record.fn_times.get('ctime'), 'unixtime', 0) or 0
                        crtime = getattr(record.fn_times.get('crtime'), 'unixtime', 0) or 0
                        
                        bodyfile.write(f"0|{record.filename or ''}|{record.recordnum}|{record.flags:04o}|0|0|"
                                     f"{record.filesize or 0}|{atime}|{mtime}|{ctime}|{crtime}\n")
                    except Exception as e:
                        logger.warning(f"Error writing record {record.recordnum} to body file: {e}")
                        bodyfile.write(f"0||{record.recordnum}|{record.flags:04o}|0|0|0|0|0|0|0\n")
        except Exception as e:
            logger.error(f"Error writing body file {output_file}: {e}")
            raise

    @staticmethod
    async def write_timeline(records: List[MftRecord], output_file: str) -> None:
        """Write records to TSK timeline format."""
        try:
            with open(output_file, 'w', encoding='utf-8') as timeline:
                for record in records:
                    try:
                        # Format: Time|Source|Type|User|Host|Short|Desc|Version|Filename|Inode|Notes|Format|Extra
                        crtime = getattr(record.fn_times.get('crtime'), 'unixtime', 0) or 0
                        mtime = getattr(record.fn_times.get('mtime'), 'unixtime', 0) or 0
                        atime = getattr(record.fn_times.get('atime'), 'unixtime', 0) or 0
                        ctime = getattr(record.fn_times.get('ctime'), 'unixtime', 0) or 0
                        
                        filename = record.filename or "Unknown"
                        
                        timeline.write(f"{crtime}|MFT|CREATE|||||{filename}|{record.recordnum}||||\n")
                        timeline.write(f"{mtime}|MFT|MODIFY|||||{filename}|{record.recordnum}||||\n")
                        timeline.write(f"{atime}|MFT|ACCESS|||||{filename}|{record.recordnum}||||\n")
                        timeline.write(f"{ctime}|MFT|CHANGE|||||{filename}|{record.recordnum}||||\n")
                    except Exception as e:
                        logger.warning(f"Error writing record {record.recordnum} to timeline: {e}")
        except Exception as e:
            logger.error(f"Error writing timeline file {output_file}: {e}")
            raise

    @staticmethod
    async def write_l2t(records: List[MftRecord], output_file: str) -> None:
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as l2tfile:
                writer = csv.writer(l2tfile)
                writer.writerow(['date', 'time', 'timezone', 'MACB', 'source', 'sourcetype', 'type', 'user', 'host', 'short', 'desc', 'version', 'filename', 'inode', 'notes', 'format', 'extra'])
                
                for record in records:
                    try:
                        filename = record.filename or "Unknown"
                        
                        for time_type, time_obj in record.fn_times.items():
                            if time_obj is None:
                                continue
                                
                            try:
                                macb = 'M' if time_type == 'mtime' else 'A' if time_type == 'atime' else 'C' if time_type == 'ctime' else 'B'
                                date_str = time_obj.dt.strftime('%m/%d/%Y') if time_obj.dt else ''
                                time_str = time_obj.dt.strftime('%H:%M:%S') if time_obj.dt else ''
                                
                                writer.writerow([
                                    date_str, time_str, 'UTC', macb, 'MFT', 'FILESYSTEM', time_type, '', '', '',
                                    f"{filename} {time_type}", '', filename, record.recordnum, '', '', ''
                                ])
                            except Exception as time_e:
                                logger.warning(f"Error processing time {time_type} for record {record.recordnum}: {time_e}")
                    except Exception as e:
                        logger.warning(f"Error writing record {record.recordnum} to l2t: {e}")
        except Exception as e:
            logger.error(f"Error writing l2t file {output_file}: {e}")
            raise

    @staticmethod
    @contextmanager
    def _get_db_connection(db_path: str):
        conn = None
        try:
            conn = sqlite3.connect(db_path)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()

    @staticmethod
    async def write_sqlite(records: List[MftRecord], output_file: str) -> None:
        try:
            with FileWriters._get_db_connection(output_file) as conn:
                cursor = conn.cursor()

                # Create and populate static tables
                sql_dir = os.path.join(os.path.dirname(__file__), 'sql')
                if os.path.exists(sql_dir):
                    for sql_file in os.listdir(sql_dir):
                        if sql_file.endswith('.sql'):
                            try:
                                with open(os.path.join(sql_dir, sql_file), 'r') as f:
                                    cursor.executescript(f.read())
                            except Exception as e:
                                logger.warning(f"Error executing SQL script {sql_file}: {e}")

                # Create MFT records table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS mft_records (
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
                    try:
                        cursor.execute('''
                            INSERT OR REPLACE INTO mft_records (
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
                            getattr(record.fn_times.get('crtime'), 'dtstr', '') if record.fn_times.get('crtime') else '',
                            getattr(record.fn_times.get('mtime'), 'dtstr', '') if record.fn_times.get('mtime') else '',
                            getattr(record.fn_times.get('atime'), 'dtstr', '') if record.fn_times.get('atime') else '',
                            getattr(record.fn_times.get('ctime'), 'dtstr', '') if record.fn_times.get('ctime') else '',
                            ','.join(map(str, record.attribute_types)) if record.attribute_types else ''
                        ))
                    except Exception as e:
                        logger.warning(f"Error inserting record {record.recordnum} into database: {e}")

                conn.commit()
        except Exception as e:
            logger.error(f"Error writing SQLite database {output_file}: {e}")
            raise

    @staticmethod
    async def write_tsk(records: List[MftRecord], output_file: str) -> None:
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as tskfile:
                for record in records:
                    try:
                        # TSK body file format:
                        # MD5|name|inode|mode_as_string|UID|GID|size|atime|mtime|ctime|crtime
                        atime = getattr(record.fn_times.get('atime'), 'unixtime', 0) or 0
                        mtime = getattr(record.fn_times.get('mtime'), 'unixtime', 0) or 0
                        ctime = getattr(record.fn_times.get('ctime'), 'unixtime', 0) or 0
                        crtime = getattr(record.fn_times.get('crtime'), 'unixtime', 0) or 0
                        
                        tskfile.write(f"0|{record.filename or ''}|{record.recordnum}|{record.flags:04o}|0|0|"
                                    f"{record.filesize or 0}|{atime}|{mtime}|{ctime}|{crtime}\n")
                    except Exception as e:
                        logger.warning(f"Error writing record {record.recordnum} to TSK file: {e}")
                        tskfile.write(f"0||{record.recordnum}|{record.flags:04o}|0|0|0|0|0|0|0\n")
        except Exception as e:
            logger.error(f"Error writing TSK file {output_file}: {e}")
            raise

def get_writer(format_name: str):
    writers = {
        'csv': FileWriters.write_csv,
        'json': FileWriters.write_json,
        'xml': FileWriters.write_xml,
        'excel': FileWriters.write_excel,
        'body': FileWriters.write_body,
        'timeline': FileWriters.write_timeline,
        'l2t': FileWriters.write_l2t,
        'sqlite': FileWriters.write_sqlite,
        'tsk': FileWriters.write_tsk
    }
    return writers.get(format_name.lower())