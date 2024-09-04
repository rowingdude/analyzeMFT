import pytest
import asyncio
from unittest.mock import patch, mock_open
from src.analyzeMFT.file_writers import FileWriters
from src.analyzeMFT.mft_record import MftRecord

@pytest.fixture
def mock_records():
    return [MftRecord(b'\x00' * 1024) for _ in range(5)]

@pytest.mark.asyncio
async def test_write_csv(mock_records):
    with patch('builtins.open', mock_open()) as mock_file:
        await FileWriters.write_csv(mock_records, 'output.csv')
        mock_file.assert_called_once_with('output.csv', 'w', newline='', encoding='utf-8')
        mock_file().write.assert_called()

@pytest.mark.asyncio
async def test_write_json(mock_records):
    with patch('json.dump') as mock_json_dump:
        await FileWriters.write_json(mock_records, 'output.json')
        mock_json_dump.assert_called_once()

@pytest.mark.asyncio
async def test_write_xml(mock_records):
    with patch('xml.etree.ElementTree.ElementTree.write') as mock_xml_write:
        await FileWriters.write_xml(mock_records, 'output.xml')
        mock_xml_write.assert_called_once()

@pytest.mark.asyncio
async def test_write_excel(mock_records):
    with patch('openpyxl.Workbook') as mock_workbook:
        await FileWriters.write_excel(mock_records, 'output.xlsx')
        mock_workbook.return_value.save.assert_called_once_with('output.xlsx')