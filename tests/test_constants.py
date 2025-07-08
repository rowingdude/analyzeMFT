#!/usr/bin/env python3

import pytest
from src.analyzeMFT.constants import (
    VERSION, 
    FILE_RECORD_IN_USE, 
    FILE_RECORD_IS_DIRECTORY,
    FILE_RECORD_IS_EXTENSION,
    FILE_RECORD_HAS_SPECIAL_INDEX,
    MFT_RECORD_SIZE,
    ATTRIBUTE_NAMES
)


class TestConstants:
    """Test constants module values and consistency."""
    
    def test_version_format(self):
        """Test that VERSION follows semantic versioning format."""
        assert isinstance(VERSION, str)
        assert len(VERSION) > 0
        
        # Should contain at least major.minor.patch
        parts = VERSION.split('.')
        assert len(parts) >= 3
        
        # First three parts should be numeric
        for i in range(3):
            assert parts[i].isdigit(), f"Version part {i} '{parts[i]}' is not numeric"
    
    def test_file_record_flags_values(self):
        """Test file record flag constant values."""
        # These are based on NTFS specification
        assert FILE_RECORD_IN_USE == 0x0001
        assert FILE_RECORD_IS_DIRECTORY == 0x0002
        assert FILE_RECORD_IS_EXTENSION == 0x0004
        assert FILE_RECORD_HAS_SPECIAL_INDEX == 0x0008
    
    def test_file_record_flags_types(self):
        """Test that file record flags are integers."""
        assert isinstance(FILE_RECORD_IN_USE, int)
        assert isinstance(FILE_RECORD_IS_DIRECTORY, int)
        assert isinstance(FILE_RECORD_IS_EXTENSION, int)
        assert isinstance(FILE_RECORD_HAS_SPECIAL_INDEX, int)
    
    def test_file_record_flags_uniqueness(self):
        """Test that file record flags are unique bit values."""
        flags = [
            FILE_RECORD_IN_USE,
            FILE_RECORD_IS_DIRECTORY, 
            FILE_RECORD_IS_EXTENSION,
            FILE_RECORD_HAS_SPECIAL_INDEX
        ]
        
        # Each flag should be a unique power of 2
        for i, flag in enumerate(flags):
            assert flag & (flag - 1) == 0, f"Flag {flag} is not a power of 2"
            
            # No two flags should have overlapping bits
            for j, other_flag in enumerate(flags):
                if i != j:
                    assert flag & other_flag == 0, f"Flags {flag} and {other_flag} overlap"
    
    def test_mft_record_size(self):
        """Test MFT record size constant."""
        assert MFT_RECORD_SIZE == 1024
        assert isinstance(MFT_RECORD_SIZE, int)
        assert MFT_RECORD_SIZE > 0
    
    def test_attribute_names_structure(self):
        """Test ATTRIBUTE_NAMES structure and contents."""
        assert isinstance(ATTRIBUTE_NAMES, dict)
        assert len(ATTRIBUTE_NAMES) > 0
        
        # Check for essential NTFS attributes
        essential_attributes = [
            0x10,  # STANDARD_INFORMATION
            0x20,  # ATTRIBUTE_LIST
            0x30,  # FILE_NAME
            0x40,  # OBJECT_ID
            0x50,  # SECURITY_DESCRIPTOR
            0x60,  # VOLUME_NAME
            0x70,  # VOLUME_INFORMATION
            0x80,  # DATA
            0x90,  # INDEX_ROOT
            0xA0,  # INDEX_ALLOCATION
            0xB0,  # BITMAP
            0xC0,  # REPARSE_POINT
            0xD0,  # EA_INFORMATION
            0xE0,  # EA
            0x100, # LOGGED_UTILITY_STREAM
        ]
        
        for attr_type in essential_attributes:
            assert attr_type in ATTRIBUTE_NAMES, f"Missing attribute type 0x{attr_type:02X}"
    
    def test_attribute_names_values(self):
        """Test ATTRIBUTE_NAMES values are strings."""
        for attr_type, attr_name in ATTRIBUTE_NAMES.items():
            assert isinstance(attr_type, int), f"Attribute type {attr_type} should be int"
            assert isinstance(attr_name, str), f"Attribute name {attr_name} should be str"
            assert len(attr_name) > 0, f"Attribute name for type {attr_type} is empty"
    
    def test_attribute_names_known_values(self):
        """Test specific known attribute type mappings."""
        expected_mappings = {
            0x10: "$STANDARD_INFORMATION",
            0x20: "$ATTRIBUTE_LIST", 
            0x30: "$FILE_NAME",
            0x40: "$OBJECT_ID",
            0x50: "$SECURITY_DESCRIPTOR",
            0x60: "$VOLUME_NAME",
            0x70: "$VOLUME_INFORMATION",
            0x80: "$DATA",
            0x90: "$INDEX_ROOT",
            0xA0: "$INDEX_ALLOCATION",
            0xB0: "$BITMAP",
            0xC0: "$REPARSE_POINT",
            0xD0: "$EA_INFORMATION",
            0xE0: "$EA",
            0x100: "$LOGGED_UTILITY_STREAM"
        }
        
        for attr_type, expected_name in expected_mappings.items():
            assert attr_type in ATTRIBUTE_NAMES
            assert ATTRIBUTE_NAMES[attr_type] == expected_name
    
    def test_flag_combinations(self):
        """Test that file record flags can be combined properly."""
        # Test combining IN_USE and DIRECTORY flags
        combined = FILE_RECORD_IN_USE | FILE_RECORD_IS_DIRECTORY
        
        # Should be able to test individual flags
        assert combined & FILE_RECORD_IN_USE
        assert combined & FILE_RECORD_IS_DIRECTORY
        assert not (combined & FILE_RECORD_IS_EXTENSION)
        
        # Test three flag combination
        three_flags = FILE_RECORD_IN_USE | FILE_RECORD_IS_DIRECTORY | FILE_RECORD_HAS_SPECIAL_INDEX
        assert three_flags & FILE_RECORD_IN_USE
        assert three_flags & FILE_RECORD_IS_DIRECTORY
        assert three_flags & FILE_RECORD_HAS_SPECIAL_INDEX
        assert not (three_flags & FILE_RECORD_IS_EXTENSION)
    
    def test_constants_immutability(self):
        """Test that constants maintain their expected values."""
        # These should never change as they're based on NTFS specification
        assert FILE_RECORD_IN_USE == 1
        assert FILE_RECORD_IS_DIRECTORY == 2
        assert FILE_RECORD_IS_EXTENSION == 4
        assert FILE_RECORD_HAS_SPECIAL_INDEX == 8
        assert MFT_RECORD_SIZE == 1024