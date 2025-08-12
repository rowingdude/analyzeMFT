#!/usr/bin/env python3

import pytest
import hashlib
import zlib
import logging
from unittest.mock import Mock, patch
from src.analyzeMFT.hash_processor import HashProcessor, HashResult


class TestHashResult:
    """Test HashResult dataclass functionality."""

    def test_hash_result_initialization(self):
        """Test HashResult initialization with valid values."""
        result = HashResult(
            record_index=0,
            md5="d41d8cd98f00b204e9800998ecf8427e",
            sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            sha512="cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e",
            crc32="00000000",
            processing_time=0.001
        )

        assert result.record_index == 0
        assert result.md5 == "d41d8cd98f00b204e9800998ecf8427e"
        assert result.sha256 == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert result.sha512 == "cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e"
        assert result.crc32 == "00000000"
        assert result.processing_time == 0.001

    def test_hash_result_equality(self):
        """Test HashResult equality comparison."""
        result1 = HashResult(0, "md5_1", "sha256_1", "sha512_1", "crc32_1", 0.001)
        result2 = HashResult(0, "md5_1", "sha256_1", "sha512_1", "crc32_1", 0.001)
        result3 = HashResult(0, "md5_2", "sha256_1", "sha512_1", "crc32_1", 0.001)

        assert result1 == result2
        assert result1 != result3


class TestHashProcessor:
    """Test HashProcessor class functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.logger = logging.getLogger('test_hash_processor')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(logging.NullHandler())  # Avoid log output

    def test_hash_processor_initialization_default(self):
        """Test HashProcessor initialization with defaults."""
        with patch('multiprocessing.cpu_count', return_value=8):
            processor = HashProcessor()
            assert processor.num_processes > 0
            assert processor.num_processes <= 8
            assert processor.logger is not None

    def test_hash_processor_initialization_custom(self):
        """Test HashProcessor initialization with custom parameters."""
        processor = HashProcessor(num_processes=4, logger=self.logger)
        assert processor.num_processes == 4
        assert processor.logger is self.logger

    def test_hash_processor_initialization_auto_detect_high_core_count(self):
        """Test HashProcessor CPU core auto-detection with high core count."""
        with patch('multiprocessing.cpu_count', return_value=16):
            processor = HashProcessor()
            assert processor.num_processes == 8

    def test_hash_processor_initialization_auto_detect_low_core_count(self):
        """Test HashProcessor CPU core auto-detection with low core count."""
        with patch('multiprocessing.cpu_count', return_value=2):
            processor = HashProcessor()
            assert processor.num_processes == 2

    def test_hash_processor_initialization_cpu_count_unavailable(self):
        """Test HashProcessor fallback when cpu_count is unavailable."""
        with patch('multiprocessing.cpu_count', side_effect=NotImplementedError):
            processor = HashProcessor()
            assert processor.num_processes == 1

    def test_compute_hashes_single_record(self):
        """Test computing hashes for a single record."""
        processor = HashProcessor(num_processes=1, logger=self.logger)
        test_data = b"Hello, World!"
        records = [test_data]

        results = processor.compute_hashes_single_threaded(records)

        assert len(results) == 1
        result = results[0]
        expected_md5 = hashlib.md5(test_data).hexdigest()
        expected_sha256 = hashlib.sha256(test_data).hexdigest()
        expected_sha512 = hashlib.sha512(test_data).hexdigest()
        expected_crc32 = f"{zlib.crc32(test_data) & 0xffffffff:08x}"

        assert result.md5 == expected_md5
        assert result.sha256 == expected_sha256
        assert result.sha512 == expected_sha512
        assert result.crc32 == expected_crc32
        assert result.record_index == 0
        assert result.processing_time >= 0

    def test_compute_hashes_multiple_records(self):
        """Test computing hashes for multiple records."""
        processor = HashProcessor(num_processes=1, logger=self.logger)
        test_records = [
            b"Record 1 data",
            b"Record 2 data with more content",
            b"Record 3 different data",
            b"Record 4 yet another set of bytes"
        ]

        results = processor.compute_hashes_single_threaded(test_records)

        assert len(results) == len(test_records)
        for i, (record_data, result) in enumerate(zip(test_records, results)):
            expected_md5 = hashlib.md5(record_data).hexdigest()
            expected_sha256 = hashlib.sha256(record_data).hexdigest()
            expected_crc32 = f"{zlib.crc32(record_data) & 0xffffffff:08x}"

            assert result.md5 == expected_md5
            assert result.sha256 == expected_sha256
            assert result.crc32 == expected_crc32
            assert result.record_index == i

    def test_compute_hashes_empty_list(self):
        """Test computing hashes for empty record list."""
        processor = HashProcessor(logger=self.logger)
        results = processor.compute_hashes_adaptive([])
        assert results == []

    def test_compute_hashes_single_threaded(self):
        """Test single-threaded hash computation."""
        processor = HashProcessor(num_processes=1, logger=self.logger)
        test_data = [b"Single threaded test data"]
        results = processor.compute_hashes_single_threaded(test_data)

        assert len(results) == 1
        result = results[0]
        assert isinstance(result, HashResult)
        expected_md5 = hashlib.md5(test_data[0]).hexdigest()
        assert result.md5 == expected_md5

    def test_compute_hashes_adaptive_small_batch(self):
        """Test adaptive processing with small batch (uses single-threaded)."""
        processor = HashProcessor(num_processes=4, logger=self.logger)
        small_batch = [b"data1", b"data2", b"data3"]

        with patch.object(processor, 'compute_hashes_single_threaded') as mock_single:
            mock_single.return_value = [
                HashResult(i, "md5", "sha256", "sha512", "crc32", 0.001)
                for i in range(len(small_batch))
            ]
            results = processor.compute_hashes_adaptive(small_batch)
            mock_single.assert_called_once_with(small_batch)
            assert len(results) == 3

    def test_compute_hashes_adaptive_large_batch(self):
        """Test adaptive processing with large batch (uses multiprocessed)."""
        processor = HashProcessor(num_processes=2, logger=self.logger)
        large_batch = [f"data{i}".encode() for i in range(50)]  # Above threshold

        with patch.object(processor, 'compute_hashes_multiprocessed') as mock_multi:
            with patch('multiprocessing.cpu_count', return_value=2):  # Mock low CPU count to trigger multiprocessing
                mock_multi.return_value = [
                    HashResult(i, "md5", "sha256", "sha512", "crc32", 0.001)
                    for i in range(len(large_batch))
                ]
                results = processor.compute_hashes_adaptive(large_batch)
                mock_multi.assert_called_once_with(large_batch)
                assert len(results) == 50

    def test_compute_hashes_different_data_types(self):
        """Test computing hashes for different types of binary data."""
        processor = HashProcessor(num_processes=1, logger=self.logger)
        test_cases = [
            b"",
            b"a",
            b"Hello" * 1000,
            bytes(range(256)),
            b"\x00" * 1024,
        ]

        results = processor.compute_hashes_single_threaded(test_cases)

        assert len(results) == len(test_cases)
        for i, result in enumerate(results):
            assert isinstance(result, HashResult)
            assert len(result.md5) == 32
            assert len(result.sha256) == 64
            assert len(result.sha512) == 128
            assert len(result.crc32) == 8
            assert result.record_index == i

    def test_compute_hashes_large_record(self):
        """Test computing hashes for large individual record."""
        processor = HashProcessor(num_processes=1, logger=self.logger)
        large_data = b"A" * (1024 * 1024)  # 1MB
        records = [large_data]

        results = processor.compute_hashes_single_threaded(records)

        assert len(results) == 1
        result = results[0]
        expected_md5 = hashlib.md5(large_data).hexdigest()
        assert result.md5 == expected_md5
        assert result.record_index == 0

    def test_compute_hashes_deterministic(self):
        """Test that hash computation is deterministic."""
        processor1 = HashProcessor(num_processes=1, logger=self.logger)
        processor2 = HashProcessor(num_processes=1, logger=self.logger)

        test_data = [b"test data 1", b"test data 2", b"test data 3"]
        results1 = processor1.compute_hashes_single_threaded(test_data)
        results2 = processor2.compute_hashes_single_threaded(test_data)

        assert len(results1) == len(results2)
        for r1, r2 in zip(results1, results2):
            # Compare everything except processing_time
            assert r1.record_index == r2.record_index
            assert r1.md5 == r2.md5
            assert r1.sha256 == r2.sha256
            assert r1.sha512 == r2.sha512
            assert r1.crc32 == r2.crc32

    def test_performance_statistics(self):
        """Test that performance statistics are tracked."""
        processor = HashProcessor(num_processes=1, logger=self.logger)
        test_data = [b"data1", b"data2", b"data3"]
        processor.compute_hashes_single_threaded(test_data)
        stats = processor.get_performance_stats()

        assert stats['total_records'] == 3
        assert stats['total_processing_time'] >= 0
        assert stats['average_time_per_record'] >= 0

    def test_error_handling_invalid_data(self):
        """Test error handling for invalid input data."""
        processor = HashProcessor(num_processes=1, logger=self.logger)

        # Invalid: None in list - should handle gracefully or raise specific exception
        try:
            results = processor.compute_hashes_single_threaded([b"valid", None])
            # If it doesn't raise, check that it handles None gracefully
            assert len(results) == 2
        except (AttributeError, TypeError):
            # Expected to fail with these exceptions
            pass

        # Invalid: non-bytes type - should handle gracefully or raise specific exception
        try:
            results = processor.compute_hashes_single_threaded([123, b"valid"])
            # If it doesn't raise, check that it handles non-bytes gracefully
            assert len(results) == 2
        except (AttributeError, TypeError):
            # Expected to fail with these exceptions
            pass

    def test_hash_processor_with_zero_processes(self):
        """Test HashProcessor defaults to 1 if num_processes <= 0."""
        processor = HashProcessor(num_processes=0, logger=self.logger)
        assert processor.num_processes == 1

        processor = HashProcessor(num_processes=-5, logger=self.logger)
        assert processor.num_processes == 1

    def test_compute_hashes_order_preservation(self):
        """Test that hash results maintain input order."""
        processor = HashProcessor(num_processes=2, logger=self.logger)
        test_records = [f"record_{i:03d}".encode() for i in range(10)]
        results = processor.compute_hashes_single_threaded(test_records)

        assert len(results) == len(test_records)
        for i, (record_data, result) in enumerate(zip(test_records, results)):
            expected_md5 = hashlib.md5(record_data).hexdigest()
            assert result.md5 == expected_md5
            assert result.record_index == i