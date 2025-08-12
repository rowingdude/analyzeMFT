"""
Input validation module for analyzeMFT.

This module provides comprehensive input validation functions to prevent
security vulnerabilities and ensure data integrity in MFT analysis.

Security features:
- MFT magic number validation
- Path traversal protection  
- Numeric bounds checking
- Buffer overflow prevention
- Configuration schema validation
"""

import os
import struct
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, Union
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    pass

class MFTValidationError(ValidationError):
    pass

class PathValidationError(ValidationError):
    pass

class NumericValidationError(ValidationError):
    pass

class ConfigValidationError(ValidationError):
    pass

MAX_FILE_SIZE_GB = 10
MIN_CHUNK_SIZE = 1
MAX_CHUNK_SIZE = 50000
MIN_HASH_PROCESSES = 1
MAX_HASH_PROCESSES = 32
MIN_TEST_RECORDS = 1
MAX_TEST_RECORDS = 1000000
MFT_RECORD_SIZE = 1024
MFT_MAGIC_SIGNATURE = b'FILE'

def validate_mft_file(file_path: str) -> Path:
    """
    Validate MFT file for security and integrity.
    
    Args:
        file_path: Path to the MFT file
        
    Returns:
        Resolved Path object
        
    Raises:
        MFTValidationError: If file validation fails
    """
    try:
        path = Path(file_path).resolve()
        
        if not path.exists():
            raise FileNotFoundError(f"MFT file not found: {file_path}")
            
        if not path.is_file():
            raise MFTValidationError(f"Path is not a file: {file_path}")
            
        if not os.access(path, os.R_OK):
            raise PermissionError(f"Cannot read MFT file: {file_path}")
            
        file_size = path.stat().st_size
        max_size = MAX_FILE_SIZE_GB * 1024**3
        
        if file_size == 0:
            raise MFTValidationError(f"MFT file is empty: {file_path}")
            
        if file_size > max_size:
            raise MFTValidationError(
                f"MFT file too large ({file_size / 1024**3:.1f}GB > {MAX_FILE_SIZE_GB}GB): {file_path}"
            )
            
        if file_size < MFT_RECORD_SIZE:
            raise MFTValidationError(
                f"MFT file too small ({file_size} bytes < {MFT_RECORD_SIZE} bytes): {file_path}"
            )
            
        try:
            with open(path, 'rb') as f:
                magic = f.read(4)
                if magic != MFT_MAGIC_SIGNATURE:
                    logger.warning(
                        f"File does not start with expected MFT signature 'FILE': {file_path}. "
                        f"Found: {magic.hex() if magic else 'empty'}. Proceeding with analysis."
                    )
        except IOError as e:
            raise MFTValidationError(f"Cannot read MFT file header: {e}")
            
        logger.info(f"MFT file validation successful: {file_path} ({file_size:,} bytes)")
        return path
        
    except (OSError, IOError) as e:
        raise MFTValidationError(f"MFT file validation failed: {e}")

def validate_output_path(output_path: str) -> Path:
    """
    Validate output path for security.
    
    Args:
        output_path: Path to the output file
        
    Returns:
        Resolved Path object
        
    Raises:
        PathValidationError: If path validation fails
    """
    try:
        if '..' in output_path:
            raise PathValidationError(
                f"Path traversal detected in output path: {output_path}"
            )
        
        path = Path(output_path).resolve()
        parent_dir = path.parent
        
        if not parent_dir.exists():
            raise PathValidationError(
                f"Output directory does not exist: {parent_dir}"
            )
            
        if not os.access(parent_dir, os.W_OK):
            raise PermissionError(
                f"Cannot write to output directory: {parent_dir}"
            )
            
        if path.exists():
            logger.warning(f"Output file already exists and will be overwritten: {output_path}")
            
        logger.info(f"Output path validation successful: {output_path}")
        return path
        
    except (OSError, IOError) as e:
        raise PathValidationError(f"Output path validation failed: {e}")

def validate_numeric_bounds(chunk_size: int, hash_processes: Optional[int] = None, 
                          test_records: int = 1000, verbosity: int = 0, debug: int = 0) -> None:
    """
    Validate numeric parameters for bounds and types.
    
    Args:
        chunk_size: Number of records to process in each chunk
        hash_processes: Number of processes for hash computation
        test_records: Number of records in test MFT
        verbosity: Verbosity level
        debug: Debug level
        
    Raises:
        NumericValidationError: If validation fails
    """
    if not isinstance(chunk_size, int):
        raise NumericValidationError(f"Chunk size must be an integer, got: {type(chunk_size).__name__}")
        
    if chunk_size < MIN_CHUNK_SIZE or chunk_size > MAX_CHUNK_SIZE:
        raise NumericValidationError(
            f"Chunk size must be between {MIN_CHUNK_SIZE} and {MAX_CHUNK_SIZE}, got: {chunk_size}"
        )
        
    if hash_processes is not None:
        if not isinstance(hash_processes, int):
            raise NumericValidationError(f"Hash processes must be an integer, got: {type(hash_processes).__name__}")
            
        if hash_processes < MIN_HASH_PROCESSES or hash_processes > MAX_HASH_PROCESSES:
            raise NumericValidationError(
                f"Hash processes must be between {MIN_HASH_PROCESSES} and {MAX_HASH_PROCESSES}, got: {hash_processes}"
            )
            
    if not isinstance(test_records, int):
        raise NumericValidationError(f"Test records must be an integer, got: {type(test_records).__name__}")
        
    if test_records < MIN_TEST_RECORDS or test_records > MAX_TEST_RECORDS:
        raise NumericValidationError(
            f"Test records must be between {MIN_TEST_RECORDS:,} and {MAX_TEST_RECORDS:,}, got: {test_records:,}"
        )
        
    if not isinstance(verbosity, int) or verbosity < 0 or verbosity > 5:
        raise NumericValidationError(f"Verbosity level must be between 0 and 5, got: {verbosity}")
        
    if not isinstance(debug, int) or debug < 0 or debug > 5:
        raise NumericValidationError(f"Debug level must be between 0 and 5, got: {debug}")
    
    logger.debug(f"Numeric validation successful: chunk_size={chunk_size}, hash_processes={hash_processes}, "
                f"test_records={test_records}, verbosity={verbosity}, debug={debug}")

def validate_export_format(export_format: str, output_file: str) -> str:
    """
    Validate export format and check file extension compatibility.
    
    Args:
        export_format: Export format name
        output_file: Output file path
        
    Returns:
        Validated export format
        
    Raises:
        ValidationError: If validation fails
    """
    valid_formats = ['csv', 'json', 'xml', 'excel', 'body', 'timeline', 'l2t', 'sqlite', 'tsk']
    
    if export_format not in valid_formats:
        raise ValidationError(f"Invalid export format: {export_format}. Valid formats: {', '.join(valid_formats)}")
        
    ext_mapping = {
        'csv': ['.csv'],
        'json': ['.json'],
        'xml': ['.xml'],
        'excel': ['.xlsx', '.xls'],
        'sqlite': ['.db', '.sqlite', '.sqlite3'],
        'body': ['.body'],
        'timeline': ['.timeline'],
        'l2t': ['.csv'],
        'tsk': ['.body', '.bodyfile']
    }
    
    if export_format in ext_mapping:
        expected_exts = ext_mapping[export_format]
        output_ext = Path(output_file).suffix.lower()
        if output_ext not in expected_exts and output_ext != "":
            logger.warning(f"Output file extension '{output_ext}' may not match export format '{export_format}'. "
                          f"Expected: {', '.join(expected_exts)}")
    
    if export_format == 'excel':
        try:
            import openpyxl
        except ImportError:
            raise ValidationError("Excel export requires 'openpyxl' package. Install with: pip install openpyxl")
    
    logger.debug(f"Export format validation successful: {export_format}")
    return export_format

def validate_attribute_length(attr_len: int, offset: int, record_size: int, attr_type: int = None) -> None:
    """
    Validate attribute length against record boundaries.
    
    Args:
        attr_len: Attribute length
        offset: Attribute offset in record
        record_size: Total record size
        attr_type: Attribute type (for logging)
        
    Raises:
        ValidationError: If validation fails
    """
    if attr_len <= 0:
        raise ValidationError(f"Invalid attribute length: {attr_len} (must be > 0)")
        
    if attr_len > record_size:
        raise ValidationError(f"Attribute length {attr_len} exceeds record size {record_size}")
        
    if offset + attr_len > record_size:
        raise ValidationError(
            f"Attribute extends beyond record boundary: offset={offset}, length={attr_len}, "
            f"record_size={record_size}"
        )
        
    if attr_len > record_size // 2:
        logger.warning(f"Large attribute detected: type={attr_type}, length={attr_len}, "
                      f"record_size={record_size}")

def validate_config_schema(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate configuration dictionary against schema.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Validated configuration dictionary
        
    Raises:
        ConfigValidationError: If validation fails
    """
    schema = {
        'chunk_size': {'type': int, 'min': MIN_CHUNK_SIZE, 'max': MAX_CHUNK_SIZE},
        'verbosity': {'type': int, 'min': 0, 'max': 5},
        'debug': {'type': int, 'min': 0, 'max': 5},
        'export_format': {'type': str, 'allowed': ['csv', 'json', 'xml', 'excel', 'body', 'timeline', 'l2t', 'sqlite', 'tsk']},
        'compute_hashes': {'type': bool},
        'multiprocessing_hashes': {'type': bool},
        'hash_processes': {'type': int, 'min': MIN_HASH_PROCESSES, 'max': MAX_HASH_PROCESSES, 'optional': True},
        'file_size_threshold_mb': {'type': int, 'min': 1, 'max': 10000, 'optional': True}
    }
    
    validated_config = {}
    
    for key, value in config.items():
        if key not in schema:
            logger.warning(f"Unknown configuration key: {key}")
            continue
            
        rules = schema[key]
        expected_type = rules['type']
        
        if not isinstance(value, expected_type):
            raise ConfigValidationError(
                f"Configuration key '{key}' must be {expected_type.__name__}, got: {type(value).__name__}"
            )
            
        if expected_type == int:
            if 'min' in rules and value < rules['min']:
                raise ConfigValidationError(f"Configuration key '{key}' must be >= {rules['min']}, got: {value}")
            if 'max' in rules and value > rules['max']:
                raise ConfigValidationError(f"Configuration key '{key}' must be <= {rules['max']}, got: {value}")
                
        if expected_type == str and 'allowed' in rules:
            if value not in rules['allowed']:
                raise ConfigValidationError(
                    f"Configuration key '{key}' must be one of {rules['allowed']}, got: {value}"
                )
        
        validated_config[key] = value
    
    logger.debug(f"Configuration validation successful: {len(validated_config)} keys validated")
    return validated_config

def validate_paths_secure(input_file: str, output_file: str) -> Tuple[Path, Path]:
    """
    Validate both input and output paths for security.
    
    Args:
        input_file: Input file path
        output_file: Output file path
        
    Returns:
        Tuple of validated input and output Path objects
        
    Raises:
        PathValidationError: If validation fails
    """
    input_path = validate_mft_file(input_file)
    output_path = validate_output_path(output_file)
    
    if input_path == output_path:
        raise PathValidationError("Input and output files cannot be the same")
    
    return input_path, output_path