import csv
import json
import xml.etree.ElementTree as ET
import asyncio
from typing import List, Dict, Any
from .mft_record import MftRecord

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