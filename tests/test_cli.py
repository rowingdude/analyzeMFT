import pytest
from unittest.mock import patch, MagicMock
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
        yield mock

@pytest.fixture
def mock_stdout():
    with patch('sys.stdout', new=StringIO()) as fake_out:
        yield fake_out

@pytest.mark.asyncio
async def test_main_with_valid_arguments(mock_analyzer, mock_stdout):
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.csv']
    with patch.object(sys, 'argv', test_args):
        await main()
    
    mock_analyzer.assert_called_once_with('test.mft', 'output.csv', False, False, 'csv')
    mock_analyzer.return_value.analyze.assert_called_once()
    assert "Analysis complete. Results written to output.csv" in mock_stdout.getvalue()

@pytest.mark.asyncio
async def test_main_with_missing_arguments(mock_stdout):
    test_args = ['analyzeMFT.py']
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit):
            await main()
    
    assert "Usage:" in mock_stdout.getvalue()

@pytest.mark.asyncio
@pytest.mark.parametrize("export_format", ['csv', 'json', 'xml', 'excel', 'body', 'timeline', 'l2t'])
async def test_main_with_different_export_formats(mock_analyzer, export_format):
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', f'output.{export_format}', f'--{export_format}']
    with patch.object(sys, 'argv', test_args):
        await main()
    
    mock_analyzer.assert_called_once_with('test.mft', f'output.{export_format}', False, False, export_format)

@pytest.mark.asyncio
async def test_main_with_debug_option(mock_analyzer):
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.csv', '-d']
    with patch.object(sys, 'argv', test_args):
        await main()
    
    mock_analyzer.assert_called_once_with('test.mft', 'output.csv', True, False, 'csv')

@pytest.mark.asyncio
async def test_main_with_hash_option(mock_analyzer):
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.csv', '-H']
    with patch.object(sys, 'argv', test_args):
        await main()
    
    mock_analyzer.assert_called_once_with('test.mft', 'output.csv', False, True, 'csv')

@pytest.mark.asyncio
async def test_main_with_version_option(mock_stdout):
    test_args = ['analyzeMFT.py', '--version']
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit):
            await main()
    
    assert VERSION in mock_stdout.getvalue()

@pytest.mark.asyncio
async def test_main_with_analyzer_exception(mock_analyzer, mock_stdout):
    mock_analyzer.return_value.analyze.side_effect = Exception("Test error")
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.csv']
    with patch.object(sys, 'argv', test_args):
        await main()
    
    assert "An unexpected error occurred: Test error" in mock_stdout.getvalue()

@pytest.mark.asyncio
async def test_main_with_keyboard_interrupt(mock_analyzer, mock_stdout):
    mock_analyzer.return_value.analyze.side_effect = KeyboardInterrupt()
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.csv']
    with patch.object(sys, 'argv', test_args):
        await main()
    
    assert "Operation interrupted by user" in mock_stdout.getvalue()

@pytest.mark.asyncio
async def test_main_with_windows_event_loop_policy():
    with patch('sys.platform', 'win32'):
        with patch('asyncio.set_event_loop_policy') as mock_set_policy:
            test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.csv']
            with patch.object(sys, 'argv', test_args):
                await main()
            
            mock_set_policy.assert_called_once_with(asyncio.WindowsProactorEventLoopPolicy())

@pytest.mark.asyncio
async def test_main_with_non_windows_platform():
    with patch('sys.platform', 'linux'):
        with patch('asyncio.set_event_loop_policy') as mock_set_policy:
            test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.csv']
            with patch.object(sys, 'argv', test_args):
                await main()
            
            mock_set_policy.assert_not_called()

def test_main_with_invalid_file_path():
    test_args = ['analyzeMFT.py', '-f', 'nonexistent.mft', '-o', 'output.csv']
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit):
            asyncio.run(main())

def test_main_with_unsupported_export_format():
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.unsupported', '--unsupported']
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit):
            asyncio.run(main())

@pytest.mark.asyncio
async def test_interrupt_handling():
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.csv']
    with patch.object(sys, 'argv', test_args):
        with patch('src.analyzeMFT.cli.MftAnalyzer') as mock_analyzer:
            mock_analyzer.return_value.analyze.side_effect = KeyboardInterrupt()
            await main()
            assert "Operation interrupted by user" in capsys.readouterr().out