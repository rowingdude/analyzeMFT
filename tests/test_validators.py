"""Tests for input validation module."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from src.analyzeMFT.validators import (
    validate_mft_file, validate_output_path, validate_numeric_bounds,
    validate_export_format, validate_attribute_length, validate_config_schema,
    validate_paths_secure, ValidationError, MFTValidationError, 
    PathValidationError, NumericValidationError, ConfigValidationError
)

class TestMFTFileValidation:
    
    def test_validate_mft_file_nonexistent(self):
        """Test validation fails for non-existent file"""
        with pytest.raises(MFTValidationError, match="MFT file not found"):
            validate_mft_file("nonexistent.mft")
    
    def test_validate_mft_file_empty(self):
        """Test validation fails for empty file"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            with pytest.raises(MFTValidationError, match="MFT file is empty"):
                validate_mft_file(tmp_path)
        finally:
            os.unlink(tmp_path)
    
    def test_validate_mft_file_too_small(self):
        """Test validation fails for file smaller than MFT record size"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"small")
            tmp_path = tmp.name
        
        try:
            with pytest.raises(MFTValidationError, match="MFT file too small"):
                validate_mft_file(tmp_path)
        finally:
            os.unlink(tmp_path)
    
    def test_validate_mft_file_valid_with_signature(self):
        """Test validation succeeds for valid MFT file with signature"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"FILE" + b"\x00" * 1020)
            tmp_path = tmp.name
        
        try:
            result = validate_mft_file(tmp_path)
            assert result == Path(tmp_path).resolve()
        finally:
            os.unlink(tmp_path)
    
    def test_validate_mft_file_valid_without_signature(self):
        """Test validation succeeds for valid MFT file without signature (with warning)"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"XXXX" + b"\x00" * 1020)
            tmp_path = tmp.name
        
        try:
            with patch('src.analyzeMFT.validators.logger') as mock_logger:
                result = validate_mft_file(tmp_path)
                assert result == Path(tmp_path).resolve()
                mock_logger.warning.assert_called_once()
        finally:
            os.unlink(tmp_path)
    
    @patch('src.analyzeMFT.validators.MAX_FILE_SIZE_GB', 0.000001)
    def test_validate_mft_file_too_large(self):
        """Test validation fails for file exceeding size limit"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"\x00" * 2048)
            tmp_path = tmp.name
        
        try:
            with pytest.raises(MFTValidationError, match="MFT file too large"):
                validate_mft_file(tmp_path)
        finally:
            os.unlink(tmp_path)

class TestOutputPathValidation:
    
    def test_validate_output_path_nonexistent_directory(self):
        """Test validation fails for non-existent parent directory"""
        with pytest.raises(PathValidationError, match="Output directory does not exist"):
            validate_output_path("/nonexistent/directory/output.csv")
    
    def test_validate_output_path_path_traversal(self):
        """Test validation fails for path traversal attempts"""
        with pytest.raises(PathValidationError, match="Path traversal detected"):
            validate_output_path("../../../etc/passwd")
    
    def test_validate_output_path_valid(self):
        """Test validation succeeds for valid output path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.csv")
            result = validate_output_path(output_path)
            assert result == Path(output_path).resolve()
    
    def test_validate_output_path_existing_file_warning(self):
        """Test warning for existing output file"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            with patch('src.analyzeMFT.validators.logger') as mock_logger:
                result = validate_output_path(tmp_path)
                assert result == Path(tmp_path).resolve()
                mock_logger.warning.assert_called_once()
        finally:
            os.unlink(tmp_path)

class TestNumericValidation:
    
    def test_validate_chunk_size_valid(self):
        """Test valid chunk size passes validation"""
        validate_numeric_bounds(chunk_size=1000)    
    def test_validate_chunk_size_too_small(self):
        """Test chunk size below minimum fails"""
        with pytest.raises(NumericValidationError, match="Chunk size must be between"):
            validate_numeric_bounds(chunk_size=0)
    
    def test_validate_chunk_size_too_large(self):
        """Test chunk size above maximum fails"""
        with pytest.raises(NumericValidationError, match="Chunk size must be between"):
            validate_numeric_bounds(chunk_size=100000)
    
    def test_validate_hash_processes_valid(self):
        """Test valid hash processes count passes validation"""
        validate_numeric_bounds(chunk_size=1000, hash_processes=4)    
    def test_validate_hash_processes_too_small(self):
        """Test hash processes below minimum fails"""
        with pytest.raises(NumericValidationError, match="Hash processes must be between"):
            validate_numeric_bounds(chunk_size=1000, hash_processes=0)
    
    def test_validate_hash_processes_too_large(self):
        """Test hash processes above maximum fails"""
        with pytest.raises(NumericValidationError, match="Hash processes must be between"):
            validate_numeric_bounds(chunk_size=1000, hash_processes=100)
    
    def test_validate_test_records_valid(self):
        """Test valid test records count passes validation"""
        validate_numeric_bounds(chunk_size=1000, test_records=500)    
    def test_validate_test_records_too_large(self):
        """Test test records above maximum fails"""
        with pytest.raises(NumericValidationError, match="Test records must be between"):
            validate_numeric_bounds(chunk_size=1000, test_records=2000000)
    
    def test_validate_verbosity_debug_levels(self):
        """Test verbosity and debug level validation"""
        validate_numeric_bounds(chunk_size=1000, verbosity=2, debug=1)        
        with pytest.raises(NumericValidationError, match="Verbosity level must be between"):
            validate_numeric_bounds(chunk_size=1000, verbosity=10)
        
        with pytest.raises(NumericValidationError, match="Debug level must be between"):
            validate_numeric_bounds(chunk_size=1000, debug=-1)

class TestExportFormatValidation:
    
    def test_validate_export_format_valid(self):
        """Test valid export formats pass validation"""
        for format_name in ['csv', 'json', 'xml', 'excel', 'body', 'timeline', 'l2t', 'sqlite', 'tsk']:
            result = validate_export_format(format_name, f"output.{format_name}")
            assert result == format_name
    
    def test_validate_export_format_invalid(self):
        """Test invalid export format fails validation"""
        with pytest.raises(ValidationError, match="Invalid export format"):
            validate_export_format("invalid", "output.invalid")
    
    def test_validate_export_format_extension_mismatch(self):
        """Test warning for format-extension mismatch"""
        with patch('src.analyzeMFT.validators.logger') as mock_logger:
            result = validate_export_format("csv", "output.txt")
            assert result == "csv"
            mock_logger.warning.assert_called_once()
    
    def test_validate_export_format_excel_dependency(self):
        """Test Excel format dependency checking"""
        with patch('builtins.__import__', side_effect=ImportError("No module named 'openpyxl'")):
            with pytest.raises(ValidationError, match="Excel export requires 'openpyxl' package"):
                validate_export_format("excel", "output.xlsx")

class TestAttributeLengthValidation:
    
    def test_validate_attribute_length_valid(self):
        """Test valid attribute length passes validation"""
        validate_attribute_length(attr_len=100, offset=50, record_size=1024)    
    def test_validate_attribute_length_zero(self):
        """Test zero attribute length fails validation"""
        with pytest.raises(ValidationError, match="Invalid attribute length: 0"):
            validate_attribute_length(attr_len=0, offset=50, record_size=1024)
    
    def test_validate_attribute_length_negative(self):
        """Test negative attribute length fails validation"""
        with pytest.raises(ValidationError, match="Invalid attribute length: -10"):
            validate_attribute_length(attr_len=-10, offset=50, record_size=1024)
    
    def test_validate_attribute_length_too_large(self):
        """Test attribute length larger than record fails validation"""
        with pytest.raises(ValidationError, match="Attribute length .* exceeds record size"):
            validate_attribute_length(attr_len=2000, offset=50, record_size=1024)
    
    def test_validate_attribute_length_extends_beyond_boundary(self):
        """Test attribute extending beyond record boundary fails validation"""
        with pytest.raises(ValidationError, match="Attribute extends beyond record boundary"):
            validate_attribute_length(attr_len=100, offset=950, record_size=1024)
    
    def test_validate_attribute_length_large_warning(self):
        """Test warning for large attributes"""
        with patch('src.analyzeMFT.validators.logger') as mock_logger:
            validate_attribute_length(attr_len=600, offset=50, record_size=1024, attr_type=144)
            mock_logger.warning.assert_called_once()

class TestConfigSchemaValidation:
    
    def test_validate_config_schema_valid(self):
        """Test valid configuration passes validation"""
        config = {
            'chunk_size': 2000,
            'verbosity': 1,
            'export_format': 'json',
            'compute_hashes': True
        }
        result = validate_config_schema(config)
        assert result == config
    
    def test_validate_config_schema_invalid_type(self):
        """Test configuration with wrong type fails validation"""
        config = {'chunk_size': 'invalid'}
        with pytest.raises(ConfigValidationError, match="must be int"):
            validate_config_schema(config)
    
    def test_validate_config_schema_out_of_range(self):
        """Test configuration with out-of-range values fails validation"""
        config = {'chunk_size': 100000}
        with pytest.raises(ConfigValidationError, match="must be <= 50000"):
            validate_config_schema(config)
    
    def test_validate_config_schema_invalid_choice(self):
        """Test configuration with invalid choice fails validation"""
        config = {'export_format': 'invalid'}
        with pytest.raises(ConfigValidationError, match="must be one of"):
            validate_config_schema(config)
    
    def test_validate_config_schema_unknown_key_warning(self):
        """Test warning for unknown configuration keys"""
        config = {'unknown_key': 'value', 'chunk_size': 1000}
        with patch('src.analyzeMFT.validators.logger') as mock_logger:
            result = validate_config_schema(config)
            assert 'unknown_key' not in result
            assert result['chunk_size'] == 1000
            mock_logger.warning.assert_called_once()

class TestPathsSecureValidation:
    
    def test_validate_paths_secure_same_file(self):
        """Test validation fails when input and output are the same file"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"FILE" + b"\x00" * 1020)
            tmp_path = tmp.name
        
        try:
            with pytest.raises(PathValidationError, match="Input and output files cannot be the same"):
                validate_paths_secure(tmp_path, tmp_path)
        finally:
            os.unlink(tmp_path)
    
    def test_validate_paths_secure_valid(self):
        """Test validation succeeds for valid input and output paths"""
        with tempfile.NamedTemporaryFile(delete=False) as input_tmp:
            input_tmp.write(b"FILE" + b"\x00" * 1020)
            input_path = input_tmp.name
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.csv")
            
            try:
                input_result, output_result = validate_paths_secure(input_path, output_path)
                assert input_result == Path(input_path).resolve()
                assert output_result == Path(output_path).resolve()
            finally:
                os.unlink(input_path)

if __name__ == "__main__":
    pytest.main([__file__])