#!/usr/bin/env python3

import pytest
import tempfile
import os
from pathlib import Path
from src.analyzeMFT.test_generator import create_test_mft
from src.analyzeMFT.constants import MFT_RECORD_SIZE


class TestTestGenerator:
    """Test the test MFT generator functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_test_mft_basic(self):
        """Test basic MFT file creation."""
        output_path = Path(self.temp_dir) / "test_basic.mft"
        
        create_test_mft(str(output_path), num_records=10, test_type="normal")        assert output_path.exists()        expected_size = 10 * MFT_RECORD_SIZE        actual_size = output_path.stat().st_size
        assert actual_size >= expected_size    
    def test_create_test_mft_normal_type(self):
        """Test creating normal type MFT file."""
        output_path = Path(self.temp_dir) / "test_normal.mft"
        
        create_test_mft(str(output_path), num_records=50, test_type="normal")
        
        assert output_path.exists()        expected_size = 50 * MFT_RECORD_SIZE
        actual_size = output_path.stat().st_size
        assert actual_size >= expected_size
    
    def test_create_test_mft_anomaly_type(self):
        """Test creating anomaly type MFT file."""
        output_path = Path(self.temp_dir) / "test_anomaly.mft"
        
        create_test_mft(str(output_path), num_records=25, test_type="anomaly")
        
        assert output_path.exists()        expected_size = 100 * MFT_RECORD_SIZE
        actual_size = output_path.stat().st_size
        assert actual_size == expected_size
    
    def test_create_test_mft_various_sizes(self):
        """Test creating MFT files of various sizes."""
        test_sizes = [1, 5, 100, 1000]
        
        for size in test_sizes:
            output_path = Path(self.temp_dir) / f"test_size_{size}.mft"
            
            create_test_mft(str(output_path), num_records=size, test_type="normal")
            
            assert output_path.exists()
            
            expected_size = size * MFT_RECORD_SIZE
            actual_size = output_path.stat().st_size
            assert actual_size >= expected_size    
    def test_create_test_mft_overwrite_existing(self):
        """Test overwriting existing MFT file."""
        output_path = Path(self.temp_dir) / "test_overwrite.mft"        create_test_mft(str(output_path), num_records=10, test_type="normal")
        initial_size = output_path.stat().st_size        create_test_mft(str(output_path), num_records=20, test_type="normal")
        new_size = output_path.stat().st_size
        
        assert new_size != initial_size
        assert new_size >= 20 * MFT_RECORD_SIZE
    
    def test_create_test_mft_path_with_spaces(self):
        """Test creating MFT file with spaces in path."""
        output_path = Path(self.temp_dir) / "test file with spaces.mft"
        
        create_test_mft(str(output_path), num_records=5, test_type="normal")
        
        assert output_path.exists()
        expected_size = 5 * MFT_RECORD_SIZE
        actual_size = output_path.stat().st_size
        assert actual_size >= expected_size
    
    def test_create_test_mft_subdirectory(self):
        """Test creating MFT file in subdirectory."""
        subdir = Path(self.temp_dir) / "subdir"
        subdir.mkdir()
        output_path = subdir / "test_subdir.mft"
        
        create_test_mft(str(output_path), num_records=15, test_type="normal")
        
        assert output_path.exists()
        expected_size = 15 * MFT_RECORD_SIZE
        actual_size = output_path.stat().st_size
        assert actual_size >= expected_size
    
    def test_create_test_mft_zero_records(self):
        """Test creating MFT file with zero records."""
        output_path = Path(self.temp_dir) / "test_zero.mft"
        
        create_test_mft(str(output_path), num_records=0, test_type="normal")
        
        assert output_path.exists()        actual_size = output_path.stat().st_size
        assert actual_size >= 0
    
    def test_create_test_mft_invalid_test_type(self):
        """Test creating MFT file with invalid test type."""
        output_path = Path(self.temp_dir) / "test_invalid.mft"        create_test_mft(str(output_path), num_records=10, test_type="invalid_type")
        
        assert output_path.exists()
        expected_size = 10 * MFT_RECORD_SIZE
        actual_size = output_path.stat().st_size
        assert actual_size >= expected_size
    
    def test_create_test_mft_large_file(self):
        """Test creating larger MFT file."""
        output_path = Path(self.temp_dir) / "test_large.mft"        num_records = 10240        
        create_test_mft(str(output_path), num_records=num_records, test_type="normal")
        
        assert output_path.exists()
        expected_size = num_records * MFT_RECORD_SIZE
        actual_size = output_path.stat().st_size
        assert actual_size >= expected_size
    
    def test_create_test_mft_file_content_structure(self):
        """Test that generated MFT file has proper record structure."""
        output_path = Path(self.temp_dir) / "test_structure.mft"
        
        create_test_mft(str(output_path), num_records=5, test_type="normal")        with open(output_path, 'rb') as f:
            data = f.read()        assert len(data) >= 5 * MFT_RECORD_SIZE        assert len(data) % MFT_RECORD_SIZE == 0
        
        num_records = len(data) // MFT_RECORD_SIZE        for i in range(min(num_records, 10)):            record_start = i * MFT_RECORD_SIZE
            record_end = record_start + MFT_RECORD_SIZE
            record_data = data[record_start:record_end]
            
            assert len(record_data) == MFT_RECORD_SIZE            assert any(byte != 0 for byte in record_data[:100])    
    def test_create_test_mft_different_extensions(self):
        """Test creating files with different extensions."""
        extensions = ['.mft', '.bin', '.dat', '']
        
        for ext in extensions:
            output_path = Path(self.temp_dir) / f"test_file{ext}"
            
            create_test_mft(str(output_path), num_records=3, test_type="normal")
            
            assert output_path.exists()
            expected_size = 3 * MFT_RECORD_SIZE
            actual_size = output_path.stat().st_size
            assert actual_size >= expected_size
    
    def test_create_test_mft_permission_error(self):
        """Test handling of permission errors."""        readonly_dir = Path(self.temp_dir) / "readonly"
        readonly_dir.mkdir()
        os.chmod(readonly_dir, 0o444)        
        output_path = readonly_dir / "test_readonly.mft"
        
        try:            with pytest.raises((PermissionError, OSError)):
                create_test_mft(str(output_path), num_records=5, test_type="normal")
        finally:            os.chmod(readonly_dir, 0o755)
    
    def test_create_test_mft_pathlib_path(self):
        """Test using pathlib.Path object as output path."""
        output_path = Path(self.temp_dir) / "test_pathlib.mft"        create_test_mft(output_path, num_records=7, test_type="normal")
        
        assert output_path.exists()
        expected_size = 7 * MFT_RECORD_SIZE
        actual_size = output_path.stat().st_size
        assert actual_size >= expected_size
    
    def test_create_test_mft_record_consistency(self):
        """Test that generated records are consistent across runs."""
        output_path1 = Path(self.temp_dir) / "test_consistent1.mft"
        output_path2 = Path(self.temp_dir) / "test_consistent2.mft"        create_test_mft(str(output_path1), num_records=10, test_type="normal")
        create_test_mft(str(output_path2), num_records=10, test_type="normal")        assert output_path1.stat().st_size == output_path2.stat().st_size        # or random elements, so we don't test for identical content