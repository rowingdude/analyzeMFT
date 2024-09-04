import pytest
import asyncio
from unittest.mock import patch, MagicMock, mock_open
from io import StringIO
from src.analyzeMFT.mft_analyzer import MftAnalyzer
from src.analyzeMFT.mft_record import MftRecord
from src.analyzeMFT.constants import MFT_RECORD_SIZE

@pytest.fixture
def mock_mft_file():
    return b'FILE' + b'\x00' * (MFT_RECORD_SIZE - 4)

@pytest.fixture
def mock_mft_record():
    record = MagicMock(spec=MftRecord)
    record.recordnum = 0
    record.filename = "test.txt"
    record.to_csv.return_value = ["0", "Valid", "In Use", "File", "1", "5", "1", "test.txt", "", "2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"]
    return record

@pytest.fixture
def analyzer():
    return MftAnalyzer("test.mft", "output.csv", debug=False, compute_hashes=False, export_format="csv")

@pytest.mark.asyncio
async def test_analyze(analyzer, mock_mft_file, mock_mft_record):
    with patch("builtins.open", mock_open(read_data=mock_mft_file)):
        with patch("src.analyzeMFT.mft_analyzer.MftRecord", return_value=mock_mft_record):
            with patch("src.analyzeMFT.mft_analyzer.FileWriters") as mock_file_writers:
                await analyzer.analyze()
                
                mock_file_writers.write_csv.assert_called_once()
                assert len(analyzer.mft_records) == 1
                assert analyzer.stats['total_records'] == 1
                assert analyzer.stats['active_records'] == 1
                assert analyzer.stats['files'] == 1

@pytest.mark.asyncio
@pytest.mark.parametrize("export_format", ["csv", "json", "xml", "excel", "body", "timeline", "l2t"])
async def test_analyze_with_different_export_formats(export_format, mock_mft_file, mock_mft_record):
    analyzer = MftAnalyzer("test.mft", f"output.{export_format}", debug=False, compute_hashes=False, export_format=export_format)
    
    with patch("builtins.open", mock_open(read_data=mock_mft_file)):
        with patch("src.analyzeMFT.mft_analyzer.MftRecord", return_value=mock_mft_record):
            with patch("src.analyzeMFT.mft_analyzer.FileWriters") as mock_file_writers:
                await analyzer.analyze()
                
                getattr(mock_file_writers, f"write_{export_format}").assert_called_once()

@pytest.mark.asyncio
async def test_analyze_with_compute_hashes(mock_mft_file, mock_mft_record):
    analyzer = MftAnalyzer("test.mft", "output.csv", debug=False, compute_hashes=True, export_format="csv")
    
    with patch("builtins.open", mock_open(read_data=mock_mft_file)):
        with patch("src.analyzeMFT.mft_analyzer.MftRecord", return_value=mock_mft_record):
            with patch("src.analyzeMFT.mft_analyzer.FileWriters"):
                await analyzer.analyze()
                
                assert 'unique_md5' in analyzer.stats
                assert 'unique_sha256' in analyzer.stats
                assert 'unique_sha512' in analyzer.stats
                assert 'unique_crc32' in analyzer.stats

@pytest.mark.asyncio
async def test_analyze_with_debug(capsys, mock_mft_file, mock_mft_record):
    analyzer = MftAnalyzer("test.mft", "output.csv", debug=True, compute_hashes=False, export_format="csv")
    
    with patch("builtins.open", mock_open(read_data=mock_mft_file)):
        with patch("src.analyzeMFT.mft_analyzer.MftRecord", return_value=mock_mft_record):
            with patch("src.analyzeMFT.mft_analyzer.FileWriters"):
                await analyzer.analyze()
                
                captured = capsys.readouterr()
                assert "Processing record 1: test.txt" in captured.out

@pytest.mark.asyncio
async def test_analyze_with_invalid_record(analyzer, mock_mft_file):
    invalid_record = b'\x00' * MFT_RECORD_SIZE
    
    with patch("builtins.open", mock_open(read_data=invalid_record)):
        with patch("src.analyzeMFT.mft_analyzer.MftRecord", side_effect=Exception("Invalid record")):
            with patch("src.analyzeMFT.mft_analyzer.FileWriters"):
                await analyzer.analyze()
                
                assert analyzer.stats['total_records'] == 1
                assert len(analyzer.mft_records) == 0

@pytest.mark.asyncio
async def test_analyze_with_interrupt(analyzer, mock_mft_file, mock_mft_record):
    with patch("builtins.open", mock_open(read_data=mock_mft_file * 2)):
        with patch("src.analyzeMFT.mft_analyzer.MftRecord", return_value=mock_mft_record):
            with patch("src.analyzeMFT.mft_analyzer.FileWriters"):
                def interrupt_analysis():
                    analyzer.interrupt_flag.set()
                
                asyncio.get_event_loop().call_later(0.1, interrupt_analysis)
                await analyzer.analyze()
                
                assert analyzer.stats['total_records'] == 1
                assert len(analyzer.mft_records) == 1

@pytest.mark.asyncio
async def test_build_filepath(analyzer, mock_mft_record):
    analyzer.mft_records = {0: mock_mft_record, 5: MagicMock(recordnum=5, filename="parent")}
    mock_mft_record.get_parent_record_num.return_value = 5
    
    filepath = analyzer.build_filepath(mock_mft_record)
    assert filepath == "\\parent\\test.txt"

@pytest.mark.asyncio
async def test_build_filepath_with_deep_path(analyzer, mock_mft_record):
    analyzer.mft_records = {i: MagicMock(recordnum=i, filename=f"dir{i}", get_parent_record_num=lambda: i+1) for i in range(300)}
    analyzer.mft_records[299].get_parent_record_num.return_value = 5
    analyzer.mft_records[5] = MagicMock(recordnum=5, filename="root", get_parent_record_num=lambda: 5)
    
    filepath = analyzer.build_filepath(analyzer.mft_records[0])
    assert filepath.startswith("DeepPath\\")
    assert len(filepath.split("\\")) == 256  # Max depth + 1 for DeepPath

@pytest.mark.asyncio
async def test_build_filepath_with_orphaned_file(analyzer, mock_mft_record):
    mock_mft_record.get_parent_record_num.return_value = mock_mft_record.recordnum
    
    filepath = analyzer.build_filepath(mock_mft_record)
    assert filepath == "\\OrphanedFiles\\test.txt"

@pytest.mark.asyncio
async def test_print_statistics(analyzer, capsys):
    analyzer.stats = {
        'total_records': 100,
        'active_records': 90,
        'directories': 10,
        'files': 80,
        'unique_md5': set(['hash1', 'hash2']),
        'unique_sha256': set(['hash3', 'hash4']),
        'unique_sha512': set(['hash5', 'hash6']),
        'unique_crc32': set(['hash7', 'hash8'])
    }
    
    analyzer.print_statistics()
    
    captured = capsys.readouterr()
    assert "Total records processed: 100" in captured.out
    assert "Active records: 90" in captured.out
    assert "Directories: 10" in captured.out
    assert "Files: 80" in captured.out
    assert "Unique MD5 hashes: 2" in captured.out
    assert "Unique SHA256 hashes: 2" in captured.out
    assert "Unique SHA512 hashes: 2" in captured.out
    assert "Unique CRC32 hashes: 2" in captured.out



@pytest.mark.asyncio
async def test_write_csv_block(analyzer, mock_mft_record):
    analyzer.mft_records = {i: mock_mft_record for i in range(1000)}
    analyzer.csv_writer = MagicMock()
    
    await analyzer.write_csv_block()
    
    assert analyzer.csv_writer.writerow.call_count == 1000
    assert len(analyzer.mft_records) == 0

@pytest.mark.asyncio
async def test_analyze_large_number_of_records(analyzer, mock_mft_file, mock_mft_record):
    large_mft_file = mock_mft_file * 10000
    with patch("builtins.open", mock_open(read_data=large_mft_file)):
        with patch("src.analyzeMFT.mft_analyzer.MftRecord", return_value=mock_mft_record):
            with patch("src.analyzeMFT.mft_analyzer.FileWriters"):
                await analyzer.analyze()
                
                assert analyzer.stats['total_records'] == 10000

@pytest.mark.asyncio
async def test_handle_interrupt(analyzer):
    with patch('asyncio.get_event_loop') as mock_loop:
        analyzer.handle_interrupt()
        mock_loop.return_value.add_signal_handler.assert_called()

@pytest.mark.asyncio
async def test_analyze_with_all_flags(mock_mft_file, mock_mft_record):
    analyzer = MftAnalyzer("test.mft", "output.csv", debug=True, compute_hashes=True, export_format="json")
    
    with patch("builtins.open", mock_open(read_data=mock_mft_file)):
        with patch("src.analyzeMFT.mft_analyzer.MftRecord", return_value=mock_mft_record):
            with patch("src.analyzeMFT.mft_analyzer.FileWriters") as mock_file_writers:
                await analyzer.analyze()
                
                mock_file_writers.write_json.assert_called_once()
                assert 'unique_md5' in analyzer.stats