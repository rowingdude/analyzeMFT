import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os
import asyncio
from io import StringIO
from src.analyzeMFT.cli import main
from src.analyzeMFT.mft_analyzer import MftAnalyzer
from src.analyzeMFT.constants import VERSION

@pytest.fixture
def mock_analyzer():
    with patch('src.analyzeMFT.cli.MftAnalyzer') as mock:
        mock.return_value.analyze = AsyncMock()
        yield mock

@pytest.fixture
def mock_stdout():
    with patch('sys.stdout', new=StringIO()) as fake_out:
        yield fake_out

@pytest.mark.asyncio
async def test_main_with_valid_arguments(mock_analyzer, mock_stdout, caplog):
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.csv']
    with patch.object(sys, 'argv', test_args):
        await main()
    
    mock_analyzer.assert_called_once_with('test.mft', 'output.csv', 0, 0, False, 'csv', None, 1000, True, None)
    mock_analyzer.return_value.analyze.assert_called_once()
    assert "Analysis complete. Results written to output.csv" in caplog.text

@pytest.mark.asyncio
async def test_main_with_missing_arguments(caplog, capsys):
    test_args = ['analyzeMFT.py']
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit):
            await main()
    
    captured = capsys.readouterr()
    assert "Usage:" in captured.out or "Error: No input file specified" in caplog.text

@pytest.mark.asyncio
@pytest.mark.parametrize("export_format", ['csv', 'json', 'xml', 'excel', 'body', 'timeline', 'l2t'])
async def test_main_with_different_export_formats(mock_analyzer, export_format):
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', f'output.{export_format}', f'--{export_format}']
    with patch.object(sys, 'argv', test_args):
        await main()
    
    mock_analyzer.assert_called_once_with('test.mft', f'output.{export_format}', 0, 0, False, export_format, None, 1000, True, None)

@pytest.mark.asyncio
async def test_main_with_debug_option(mock_analyzer):
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.csv', '-d']
    with patch.object(sys, 'argv', test_args):
        await main()
    
    mock_analyzer.assert_called_once_with('test.mft', 'output.csv', 1, 0, False, 'csv', None, 1000, True, None)

@pytest.mark.asyncio
async def test_main_with_hash_option(mock_analyzer):
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.csv', '-H']
    with patch.object(sys, 'argv', test_args):
        await main()
    
    mock_analyzer.assert_called_once_with('test.mft', 'output.csv', 0, 0, True, 'csv', None, 1000, True, None)

@pytest.mark.asyncio
async def test_main_with_version_option(capsys):
    test_args = ['analyzeMFT.py', '--version']
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit):
            await main()
    
    captured = capsys.readouterr()
    assert VERSION in captured.out

@pytest.mark.asyncio
async def test_main_with_analyzer_exception(mock_analyzer, caplog):
    mock_analyzer.return_value.analyze = AsyncMock(side_effect=Exception("Test error"))
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.csv']
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit):
            await main()
    
    assert "An unexpected error occurred: Test error" in caplog.text

@pytest.mark.asyncio
async def test_main_with_keyboard_interrupt(mock_analyzer, caplog):
    mock_analyzer.return_value.analyze = AsyncMock(side_effect=KeyboardInterrupt())
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.csv']
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit):
            await main()
    
    assert "Operation interrupted by user" in caplog.text
@pytest.mark.asyncio
async def test_main_with_non_windows_platform():
    with patch('sys.platform', 'linux'):
        with patch('asyncio.set_event_loop_policy') as mock_set_policy:
            with patch('src.analyzeMFT.cli.MftAnalyzer') as mock_analyzer:
                mock_analyzer.return_value.analyze = AsyncMock()
                test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.csv']
                with patch.object(sys, 'argv', test_args):
                    await main()
                
                mock_set_policy.assert_not_called()

def test_main_with_invalid_file_path(caplog):
    test_args = ['analyzeMFT.py', '-f', 'nonexistent.mft', '-o', 'output.csv']
    with patch.object(sys, 'argv', test_args):
        asyncio.run(main())    assert "Error reading MFT file" in caplog.text and "No such file or directory" in caplog.text

def test_main_with_unsupported_export_format():
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.unsupported', '--unsupported']
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit):
            asyncio.run(main())

@pytest.mark.asyncio
async def test_interrupt_handling(caplog):
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.csv']
    with patch.object(sys, 'argv', test_args):
        with patch('src.analyzeMFT.cli.MftAnalyzer') as mock_analyzer:
            mock_analyzer.return_value.analyze = AsyncMock(side_effect=KeyboardInterrupt())
            with pytest.raises(SystemExit):
                await main()
            assert "Operation interrupted by user" in caplog.text