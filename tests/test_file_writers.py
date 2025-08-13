import pytest
import asyncio
from unittest.mock import patch, mock_open, MagicMock, PropertyMock
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
    # Test the case where openpyxl is not available
    with patch('builtins.__import__', side_effect=ImportError("No module named 'openpyxl'")):
        with pytest.raises(ImportError, match="openpyxl is required for Excel export"):
            await FileWriters.write_excel(mock_records, 'output.xlsx')

@pytest.mark.asyncio
async def test_write_body(mock_records):
    with patch('builtins.open', mock_open()) as mock_file:
        await FileWriters.write_body(mock_records, 'output.body')
        mock_file.assert_called_once_with('output.body', 'w', encoding='utf-8')
        mock_file().write.assert_called()

@pytest.mark.asyncio
async def test_write_timeline(mock_records):
    with patch('builtins.open', mock_open()) as mock_file:
        await FileWriters.write_timeline(mock_records, 'output.timeline')
        mock_file.assert_called_once_with('output.timeline', 'w', encoding='utf-8')

@pytest.mark.asyncio
async def test_write_l2t(mock_records):
    with patch('builtins.open', mock_open()) as mock_file:
        await FileWriters.write_l2t(mock_records, 'output.l2tcsv')
        mock_file.assert_called_once_with('output.l2tcsv', 'w', newline='', encoding='utf-8')

@pytest.mark.asyncio
async def test_write_sqlite(mock_records):
    with patch('src.analyzeMFT.file_writers.FileWriters._get_db_connection') as mock_db_conn:
        mock_conn = mock_db_conn.return_value.__enter__.return_value
        mock_cursor = mock_conn.cursor.return_value
        await FileWriters.write_sqlite(mock_records, 'output.db')
        mock_db_conn.assert_called_once_with('output.db')
        mock_conn.cursor.assert_called_once()
        assert mock_cursor.execute.call_count > 0

@pytest.mark.asyncio
async def test_write_tsk(mock_records):
    with patch('builtins.open', mock_open()) as mock_file:
        await FileWriters.write_tsk(mock_records, 'output.tsk')
        mock_file.assert_called_once_with('output.tsk', 'w', newline='', encoding='utf-8')

def test_get_writer():
    from src.analyzeMFT.file_writers import get_writer, FileWriters
    
    assert get_writer('csv') == FileWriters.write_csv
    assert get_writer('json') == FileWriters.write_json
    assert get_writer('xml') == FileWriters.write_xml
    assert get_writer('excel') == FileWriters.write_excel
    assert get_writer('body') == FileWriters.write_body
    assert get_writer('timeline') == FileWriters.write_timeline
    assert get_writer('l2t') == FileWriters.write_l2t
    assert get_writer('sqlite') == FileWriters.write_sqlite
    assert get_writer('tsk') == FileWriters.write_tsk
    assert get_writer('unknown') is None

@pytest.mark.asyncio
async def test_write_csv_error_handling(mock_records):
    with patch('builtins.open', side_effect=PermissionError("Permission denied")):
        with pytest.raises(PermissionError):
            await FileWriters.write_csv(mock_records, 'output.csv')

@pytest.mark.asyncio
async def test_write_json_error_handling(mock_records):
    with patch('json.dump', side_effect=ValueError("Invalid JSON")):
        with pytest.raises(ValueError):
            await FileWriters.write_json(mock_records, 'output.json')

@pytest.mark.asyncio
async def test_write_sqlite_error_handling(mock_records):
    with patch('src.analyzeMFT.file_writers.FileWriters._get_db_connection', side_effect=Exception("Database error")):
        with pytest.raises(Exception):
            await FileWriters.write_sqlite(mock_records, 'output.db')

def test_get_db_connection():
    from src.analyzeMFT.file_writers import FileWriters
    with patch('src.analyzeMFT.file_writers.sqlite3.connect') as mock_connect:
        mock_conn = mock_connect.return_value
        # Use the context manager
        with FileWriters._get_db_connection('test.db'):
            pass
        mock_connect.assert_called_once_with('test.db')
        mock_conn.close.assert_called_once()

@pytest.mark.asyncio
async def test_write_excel_success_path(mock_records):
    # Mock openpyxl module and its classes
    with patch.dict('sys.modules', {'openpyxl': MagicMock()}):
        import sys
        mock_openpyxl = sys.modules['openpyxl']
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws
        mock_openpyxl.Workbook.return_value = mock_wb
        
        await FileWriters.write_excel(mock_records, 'output.xlsx')
        
        mock_openpyxl.Workbook.assert_called_once()
        mock_ws.append.assert_called()
        mock_wb.save.assert_called_once_with('output.xlsx')

@pytest.mark.asyncio
async def test_write_excel_record_error_handling():
    # Create mock records manually to control to_csv behavior
    mock_records = []
    for i in range(3):
        mock_record = MagicMock()
        mock_record.to_csv.side_effect = Exception("CSV conversion error")
        mock_records.append(mock_record)
    
    with patch.dict('sys.modules', {'openpyxl': MagicMock()}):
        import sys
        mock_openpyxl = sys.modules['openpyxl']
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws
        mock_openpyxl.Workbook.return_value = mock_wb
        
        await FileWriters.write_excel(mock_records, 'output.xlsx')
        
        # Should still save the workbook even with record errors
        mock_wb.save.assert_called_once_with('output.xlsx')

@pytest.mark.asyncio
async def test_write_body_time_edge_cases(mock_records):
    # Test with None times and missing attributes
    for record in mock_records:
        record.fn_times = {
            'atime': None,
            'mtime': MagicMock(unixtime=1234567890),
            'ctime': MagicMock(unixtime=None),
            'crtime': MagicMock()  # Missing unixtime attribute
        }
        delattr(record.fn_times['crtime'], 'unixtime')
        record.filename = None
        record.filesize = None
    
    with patch('builtins.open', mock_open()) as mock_file:
        await FileWriters.write_body(mock_records, 'output.body')
        mock_file.assert_called_once_with('output.body', 'w', encoding='utf-8')

@pytest.mark.asyncio
async def test_write_timeline_time_edge_cases(mock_records):
    # Test with various time configurations
    for record in mock_records:
        record.fn_times = {
            'crtime': MagicMock(unixtime=0),
            'mtime': None,
            'atime': MagicMock(),
            'ctime': MagicMock(unixtime=1234567890)
        }
        delattr(record.fn_times['atime'], 'unixtime')
        record.filename = None
    
    with patch('builtins.open', mock_open()) as mock_file:
        await FileWriters.write_timeline(mock_records, 'output.timeline')
        mock_file.assert_called_once_with('output.timeline', 'w', encoding='utf-8')

@pytest.mark.asyncio
async def test_write_l2t_time_processing():
    # Create mock records with specific time configurations
    mock_record = MagicMock()
    mock_record.filename = "test.txt"
    mock_record.recordnum = 123
    
    # Mock time object with datetime
    mock_time = MagicMock()
    mock_time.dt.strftime.side_effect = lambda fmt: "01/01/2023" if 'm' in fmt else "12:00:00"
    
    mock_record.fn_times = {
        'mtime': mock_time,
        'atime': None,  # None time should be skipped
        'ctime': mock_time,
        'crtime': mock_time
    }
    
    with patch('builtins.open', mock_open()) as mock_file:
        await FileWriters.write_l2t([mock_record], 'output.l2tcsv')
        
        # Should be called for each non-None time (3 times)
        assert mock_time.dt.strftime.call_count >= 6  # 2 calls per time (date & time)

@pytest.mark.asyncio
async def test_write_l2t_time_error_handling():
    mock_record = MagicMock()
    mock_record.filename = "test.txt"
    mock_record.recordnum = 456
    
    # Mock time object that raises exception
    mock_time = MagicMock()
    mock_time.dt.strftime.side_effect = Exception("Time format error")
    
    mock_record.fn_times = {
        'mtime': mock_time,
        'atime': mock_time
    }
    
    with patch('builtins.open', mock_open()) as mock_file:
        # Should not raise exception despite time errors
        await FileWriters.write_l2t([mock_record], 'output.l2tcsv')

@pytest.mark.asyncio
async def test_write_sqlite_with_sql_directory():
    mock_records = [MagicMock() for _ in range(3)]
    for i, record in enumerate(mock_records):
        record.recordnum = i
        record.filename = f"test{i}.txt"
        record.get_parent_record_num.return_value = 5
        record.filesize = 1024
        record.flags = 1
        record.fn_times = {
            'crtime': MagicMock(dtstr='2023-01-01'),
            'mtime': MagicMock(dtstr='2023-01-02'),
            'atime': MagicMock(dtstr='2023-01-03'),
            'ctime': MagicMock(dtstr='2023-01-04')
        }
        record.attribute_types = [16, 48, 128]
    
    with patch('src.analyzeMFT.file_writers.FileWriters._get_db_connection') as mock_db_conn:
        mock_conn = mock_db_conn.return_value.__enter__.return_value
        mock_cursor = mock_conn.cursor.return_value
        
        # Mock sql directory exists
        with patch('os.path.exists', return_value=True), \
             patch('os.listdir', return_value=['init.sql', 'tables.sql']), \
             patch('builtins.open', mock_open(read_data="CREATE TABLE test;")):
            
            await FileWriters.write_sqlite(mock_records, 'output.db')
            
            # Verify SQL scripts were executed
            assert mock_cursor.executescript.call_count == 2

@pytest.mark.asyncio
async def test_write_sqlite_sql_script_error():
    mock_records = [MagicMock()]
    
    with patch('src.analyzeMFT.file_writers.FileWriters._get_db_connection') as mock_db_conn:
        mock_conn = mock_db_conn.return_value.__enter__.return_value
        mock_cursor = mock_conn.cursor.return_value
        
        # Mock sql directory exists but script fails
        with patch('os.path.exists', return_value=True), \
             patch('os.listdir', return_value=['bad.sql']), \
             patch('builtins.open', mock_open(read_data="INVALID SQL;")):
            
            mock_cursor.executescript.side_effect = Exception("SQL Error")
            
            # Should continue despite SQL script errors
            await FileWriters.write_sqlite(mock_records, 'output.db')

@pytest.mark.asyncio
async def test_write_sqlite_record_insertion_error():
    mock_record = MagicMock()
    mock_record.recordnum = 1
    mock_record.get_parent_record_num.side_effect = Exception("Parent error")
    
    with patch('src.analyzeMFT.file_writers.FileWriters._get_db_connection') as mock_db_conn:
        mock_conn = mock_db_conn.return_value.__enter__.return_value
        mock_cursor = mock_conn.cursor.return_value
        
        with patch('os.path.exists', return_value=False):
            # Should handle record insertion errors gracefully
            await FileWriters.write_sqlite([mock_record], 'output.db')

@pytest.mark.asyncio
async def test_write_tsk_time_edge_cases():
    mock_record = MagicMock()
    mock_record.recordnum = 789
    mock_record.filename = ""  # Empty filename
    mock_record.flags = 0o755
    mock_record.filesize = None
    
    # Mix of None and missing unixtime attributes
    mock_record.fn_times = {
        'atime': None,
        'mtime': MagicMock(unixtime=1234567890),
        'ctime': MagicMock(),  # Missing unixtime
        'crtime': MagicMock(unixtime=0)
    }
    delattr(mock_record.fn_times['ctime'], 'unixtime')
    
    with patch('builtins.open', mock_open()) as mock_file:
        await FileWriters.write_tsk([mock_record], 'output.tsk')
        mock_file.assert_called_once_with('output.tsk', 'w', newline='', encoding='utf-8')

@pytest.mark.asyncio
async def test_write_tsk_record_error_handling():
    mock_record = MagicMock()
    mock_record.recordnum = 999
    mock_record.filename = "error_file.txt"
    mock_record.flags = 0o644
    mock_record.filesize = 2048
    
    # Make fn_times access throw an exception
    mock_record.fn_times = {}
    type(mock_record).fn_times = PropertyMock(side_effect=Exception("Time access error"))
    
    with patch('builtins.open', mock_open()) as mock_file:
        await FileWriters.write_tsk([mock_record], 'output.tsk')
        
        # Should write fallback line even with record errors
        handle = mock_file()
        assert handle.write.call_count >= 1

def test_get_db_connection_error_handling():
    with patch('src.analyzeMFT.file_writers.sqlite3.connect', side_effect=Exception("Connection error")):
        with pytest.raises(Exception):
            with FileWriters._get_db_connection('test.db'):
                pass

def test_get_db_connection_rollback_on_error():
    mock_conn = MagicMock()
    with patch('src.analyzeMFT.file_writers.sqlite3.connect', return_value=mock_conn):
        with pytest.raises(Exception):
            with FileWriters._get_db_connection('test.db'):
                raise Exception("Test error")
        
        mock_conn.rollback.assert_called_once()
        mock_conn.close.assert_called_once()

# Note: Excel success path test is complex due to dynamic import
# The error handling test above covers the main use case