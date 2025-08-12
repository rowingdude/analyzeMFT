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
        assert isinstance(VERSION, str), "VERSION must be a string"
        assert len(VERSION.strip()) > 0, "VERSION must not be empty"
        parts = VERSION.strip().split('.')
        assert len(parts) >= 3, "VERSION must have at least three parts (major.minor.patch)"
        for i, part in enumerate(parts[:3]):
            assert part.isdigit(), f"Version part {i} ('{part}') must be numeric"
            assert int(part) >= 0, f"Version part {i} must be non-negative"

    def test_file_record_flags_values(self):
        """Test file record flag constant values."""
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
        """Test that file record flags are unique power-of-two bit masks."""
        flags = [
            FILE_RECORD_IN_USE,
            FILE_RECORD_IS_DIRECTORY,
            FILE_RECORD_IS_EXTENSION,
            FILE_RECORD_HAS_SPECIAL_INDEX
        ]
        seen = set()
        for flag in flags:
            assert isinstance(flag, int), f"Flag {flag} is not an integer"
            assert (flag & (flag - 1)) == 0, f"Flag {hex(flag)} is not a power of 2"
            assert flag not in seen, f"Duplicate flag value {hex(flag)}"
            seen.add(flag)

    def test_mft_record_size(self):
        """Test MFT record size constant."""
        assert isinstance(MFT_RECORD_SIZE, int), "MFT_RECORD_SIZE must be an integer"
        assert MFT_RECORD_SIZE == 1024, "MFT_RECORD_SIZE must be 1024 bytes"
        assert MFT_RECORD_SIZE > 0, "MFT_RECORD_SIZE must be positive"

    def test_attribute_names_structure(self):
        """Test ATTRIBUTE_NAMES is a non-empty dictionary with expected essential attributes."""
        assert isinstance(ATTRIBUTE_NAMES, dict), "ATTRIBUTE_NAMES must be a dictionary"
        assert len(ATTRIBUTE_NAMES) > 0, "ATTRIBUTE_NAMES must not be empty"

        essential_attributes = {
            0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x80,
            0x90, 0xA0, 0xB0, 0xC0, 0xD0, 0xE0, 0x100
        }
        missing = essential_attributes - set(ATTRIBUTE_NAMES.keys())
        assert len(missing) == 0, f"Missing expected attribute types: {sorted(missing)}"

    def test_attribute_names_keys_and_values(self):
        """Test ATTRIBUTE_NAMES keys are integers and values are non-empty strings."""
        for attr_type, attr_name in ATTRIBUTE_NAMES.items():
            assert isinstance(attr_type, int), f"Attribute type {attr_type} must be an integer"
            assert isinstance(attr_name, str), f"Attribute name '{attr_name}' must be a string"
            assert len(attr_name) > 0, f"Attribute name for type {hex(attr_type)} must not be empty"
            assert attr_name.startswith('$'), f"Attribute name '{attr_name}' should start with '$'"

    def test_attribute_names_known_mappings(self):
        """Test specific NTFS attribute type to name mappings."""
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
            assert attr_type in ATTRIBUTE_NAMES, f"Missing attribute type 0x{attr_type:02X}"
            assert ATTRIBUTE_NAMES[attr_type] == expected_name, \
                f"Expected {expected_name}, got {ATTRIBUTE_NAMES[attr_type]} for type 0x{attr_type:02X}"

    def test_flag_combinations(self):
        """Test that file record flags can be combined and tested using bitwise operations."""
        combined = FILE_RECORD_IN_USE | FILE_RECORD_IS_DIRECTORY
        assert (combined & FILE_RECORD_IN_USE) != 0
        assert (combined & FILE_RECORD_IS_DIRECTORY) != 0
        assert (combined & FILE_RECORD_IS_EXTENSION) == 0

        multiple = FILE_RECORD_IN_USE | FILE_RECORD_IS_DIRECTORY | FILE_RECORD_HAS_SPECIAL_INDEX
        assert (multiple & FILE_RECORD_IN_USE) != 0
        assert (multiple & FILE_RECORD_IS_DIRECTORY) != 0
        assert (multiple & FILE_RECORD_HAS_SPECIAL_INDEX) != 0
        assert (multiple & FILE_RECORD_IS_EXTENSION) == 0

    def test_constants_hex_vs_decimal_consistency(self):
        """Test that constants are correctly defined in hexadecimal and equivalent to expected decimal values."""
        assert FILE_RECORD_IN_USE == 1
        assert FILE_RECORD_IS_DIRECTORY == 2
        assert FILE_RECORD_IS_EXTENSION == 4
        assert FILE_RECORD_HAS_SPECIAL_INDEX == 8
        assert MFT_RECORD_SIZE == 1024