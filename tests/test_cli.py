import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import asyncio
from io import StringIO
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
    with patch.object(sys, 'argv', test_args):
        await main()

    mock_analyzer.assert_called_once_with(
        mft_file='test.mft',
        output_file='output.csv',
        verbosity=0,
        debug=0,
        compute_hashes=False,
        export_format='csv',
        config_file=None,
        chunk_size=1000,
        enable_progress=True,
        analysis_profile=None
    )
    mock_analyzer.return_value.analyze.assert_called_once()
    assert "Analysis complete. Results written to output.csv" in caplog.text

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
    ('--log2timeline', 'l2t')
])
async def test_main_with_different_export_formats(mock_analyzer, export_flag, format_name):
    output_ext = 'l2tcsv' if format_name == 'l2t' else format_name
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', f'output.{output_ext}', export_flag]
    with patch.object(sys, 'argv', test_args):
        await main()

    expected_output = f'output.{output_ext}'
    mock_analyzer.assert_called_once_with(
        mft_file='test.mft',
        output_file=expected_output,
        verbosity=0,
        debug=0,
        compute_hashes=False,
        export_format=format_name,
        config_file=None,
        chunk_size=1000,
        enable_progress=True,
        analysis_profile=None
    )

@pytest.mark.asyncio
async def test_main_with_debug_option(mock_analyzer):
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.csv', '-d']
    with patch.object(sys, 'argv', test_args):
        await main()

    mock_analyzer.assert_called_once_with(
        mft_file='test.mft',
        output_file='output.csv',
        verbosity=0,
        debug=1,
        compute_hashes=False,
        export_format='csv',
        config_file=None,
        chunk_size=1000,
        enable_progress=True,
        analysis_profile=None
    )

@pytest.mark.asyncio
async def test_main_with_verbosity_option(mock_analyzer):
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.csv', '-v']
    with patch.object(sys, 'argv', test_args):
        await main()

    mock_analyzer.assert_called_once_with(
        mft_file='test.mft',
        output_file='output.csv',
        verbosity=1,
        debug=0,
        compute_hashes=False,
        export_format='csv',
        config_file=None,
        chunk_size=1000,
        enable_progress=True,
        analysis_profile=None
    )

@pytest.mark.asyncio
async def test_main_with_hash_option(mock_analyzer):
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.csv', '-H']
    with patch.object(sys, 'argv', test_args):
        await main()

    mock_analyzer.assert_called_once_with(
        mft_file='test.mft',
        output_file='output.csv',
        verbosity=0,
        debug=0,
        compute_hashes=True,
        export_format='csv',
        config_file=None,
        chunk_size=1000,
        enable_progress=True,
        analysis_profile=None
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
        with patch.object(sys, 'argv', test_args):
            await main()

        mock_analyzer.assert_called_once()

def test_main_with_invalid_file_path(caplog):
    test_args = ['analyzeMFT.py', '-f', 'nonexistent.mft', '-o', 'output.csv']
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit):
            asyncio.run(main())

    assert "Error reading MFT file" in caplog.text
    assert "No such file or directory" in caplog.text or "not found" in caplog.text

def test_main_with_config_file(mock_analyzer):
    test_args = ['analyzeMFT.py', '-f', 'test.mft', '-o', 'output.csv', '-c', 'config.json']
    with patch.object(sys, 'argv', test_args):
        asyncio.run(main())

    mock_analyzer.assert_called_once_with(
        mft_file='test.mft',
        output_file='output.csv',
        verbosity=0,
        debug=0,
        compute_hashes=False,
        export_format='csv',
        config_file='config.json',
        chunk_size=1000,
        enable_progress=True,
        analysis_profile=None
    )