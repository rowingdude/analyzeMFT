import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import asyncio
from io import StringIO
import os
from src.analyzeMFT.cli import main
from src.analyzeMFT.constants import VERSION

@pytest.fixture
def mock_analyzer():
    with patch('src.analyzeMFT.cli.MftAnalyzer') as mock:
        instance = mock.return_value
        instance.analyze = AsyncMock()
        yield mock

@pytest.fixture
def mock_stdout():
    with patch('sys.stdout', new=StringIO()) as fake_out:
        yield fake_out

@pytest.mark.asyncio
async def test_main_with_valid_arguments(mock_analyzer, caplog):
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.csv']
    with patch.object(sys, 'argv', test_args), \
         patch('os.path.abspath', side_effect=lambda x: f'/abs/{x}'):
        await main()

    mock_analyzer.assert_called_once_with(
        '/abs/test.mft',
        '/abs/output.csv',
        0,
        0,
        False,
        'csv',
        None,
        1000,
        True,
        None
    )
    mock_analyzer.return_value.analyze.assert_called_once()
    assert "Analysis complete. Results written to /abs/output.csv" in caplog.text

@pytest.mark.asyncio
async def test_main_with_missing_arguments(capsys):
    test_args = ['analyzeMFT.py']
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit):
            await main()

    captured = capsys.readouterr()
    assert "Usage:" in captured.out or "error" in captured.out.lower()

@pytest.mark.asyncio
@pytest.mark.parametrize("export_flag, format_name", [
    ('--csv', 'csv'),
    ('--json', 'json'),
    ('--xml', 'xml'),
    ('--excel', 'excel'),
    ('--body', 'body'),
    ('--timeline', 'timeline'),
    ('--l2t', 'l2t')
])
async def test_main_with_different_export_formats(mock_analyzer, export_flag, format_name):
    output_ext = 'l2tcsv' if format_name == 'l2t' else format_name
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', f'output.{output_ext}', export_flag]
    with patch.object(sys, 'argv', test_args), \
         patch('os.path.abspath', side_effect=lambda x: f'/abs/{x}'):
        await main()

    expected_output = f'/abs/output.{output_ext}'
    mock_analyzer.assert_called_once_with(
        '/abs/test.mft',
        expected_output,
        0,
        0,
        False,
        format_name,
        None,
        1000,
        True,
        None
    )

@pytest.mark.asyncio
async def test_main_with_debug_option(mock_analyzer):
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.csv', '--debug']
    with patch.object(sys, 'argv', test_args), \
         patch('os.path.abspath', side_effect=lambda x: f'/abs/{x}'):
        await main()

    mock_analyzer.assert_called_once_with(
        '/abs/test.mft',
        '/abs/output.csv',
        1,
        0,
        False,
        'csv',
        None,
        1000,
        True,
        None
    )

@pytest.mark.asyncio
async def test_main_with_verbosity_option(mock_analyzer):
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.csv', '--verbose']
    with patch.object(sys, 'argv', test_args), \
         patch('os.path.abspath', side_effect=lambda x: f'/abs/{x}'):
        await main()

    mock_analyzer.assert_called_once_with(
        '/abs/test.mft',
        '/abs/output.csv',
        1,
        0,
        False,
        'csv',
        None,
        1000,
        True,
        None
    )

@pytest.mark.asyncio
async def test_main_with_hash_option(mock_analyzer):
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.csv', '--hash']
    with patch.object(sys, 'argv', test_args), \
         patch('os.path.abspath', side_effect=lambda x: f'/abs/{x}'):
        await main()

    mock_analyzer.assert_called_once_with(
        '/abs/test.mft',
        '/abs/output.csv',
        0,
        0,
        True,
        'csv',
        None,
        1000,
        True,
        None
    )

@pytest.mark.asyncio
async def test_main_with_version_option(capsys):
    test_args = ['analyzeMFT.py', '--version']
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit):
            await main()

    captured = capsys.readouterr()
    assert VERSION in captured.out

@pytest.mark.asyncio
async def test_main_with_help_option(capsys):
    test_args = ['analyzeMFT.py', '--help']
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit):
            await main()

    captured = capsys.readouterr()
    assert "Usage:" in captured.out
    assert "-f" in captured.out
    assert "-o" in captured.out
    assert "--csv" in captured.out

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
async def test_main_with_non_windows_platform(mock_analyzer):
    with patch('sys.platform', 'linux'):
        test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.csv']
        with patch.object(sys, 'argv', test_args), \
             patch('os.path.abspath', side_effect=lambda x: f'/abs/{x}'):
            await main()

        mock_analyzer.assert_called_once()

def test_main_with_invalid_file_path(caplog):
    test_args = ['analyzeMFT.py', '-f', 'nonexistent.mft', '-o', 'output.csv']
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit):
            asyncio.run(main())

    assert ("Error reading MFT file" in caplog.text or "Validation Error" in caplog.text)
    assert ("No such file or directory" in caplog.text or "not found" in caplog.text)

def test_main_with_config_file(mock_analyzer):
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.csv', '-c', 'config.json']
    
    mock_config_data = {'profile_name': 'default', 'verbosity': 1}
    
    from src.analyzeMFT.config import AnalysisProfile
    mock_profile = AnalysisProfile(
        name="test", 
        export_format="csv",
        verbosity=1,
        chunk_size=1000
    )
    
    with patch.object(sys, 'argv', test_args), \
         patch('os.path.abspath', side_effect=lambda x: f'/abs/{x}'), \
         patch('src.analyzeMFT.config.ConfigManager.load_config_file', return_value=mock_config_data), \
         patch('src.analyzeMFT.config.ConfigManager.load_profile_from_config', return_value=mock_profile):
        asyncio.run(main())

    # The actual call arguments from the CLI
    mock_analyzer.assert_called_once()
    
    call_args = mock_analyzer.call_args[0]
    assert call_args[0].endswith('test.mft')  # filename  
    assert call_args[1].endswith('output.csv')  # output file
    assert call_args[2] == 0  # verbosity from options (not profile)
    assert call_args[3] == 1  # debug from profile  
    assert call_args[4] == False  # compute hashes
    assert call_args[5] == 'csv'  # export format
    assert call_args[6] == mock_profile  # profile object
    assert call_args[7] == 1000  # chunk size