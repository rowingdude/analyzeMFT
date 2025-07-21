#!/usr/bin/env python3

import pytest
import sqlite3
import tempfile
import logging
from pathlib import Path
from unittest.mock import Mock, patch
from src.analyzeMFT.sqlite_writer import SQLiteWriter
from src.analyzeMFT.mft_record import MftRecord


class TestSQLiteWriter:
    """Test SQLiteWriter class functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = Path(self.temp_dir) / "test.db"
        self.logger = logging.getLogger('test_sqlite')
        self.logger.setLevel(logging.DEBUG)
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_mock_record(self, record_num=0, **kwargs):
        """Create a mock MftRecord for testing."""
        defaults = {
            'recordnum': record_num,
            'filename': f'test_file_{record_num}.txt',
            'filepath': f'/test/path/test_file_{record_num}.txt',
            'file_size': 1024,
            'flags': 1,            'si_create_time': '2023-01-01 12:00:00',
            'si_modify_time': '2023-01-01 12:00:00',
            'si_access_time': '2023-01-01 12:00:00',
            'si_mft_time': '2023-01-01 12:00:00',
            'fn_create_time': '2023-01-01 12:00:00',
            'fn_modify_time': '2023-01-01 12:00:00',
            'fn_access_time': '2023-01-01 12:00:00',
            'fn_mft_time': '2023-01-01 12:00:00',
            'parent_record_num': 5,
            'notes': '',
            'sequence_number': 1,
            'used_size': 1024,
            'allocated_size': 1024,
            'base_record_number': 0,
            'next_attribute_id': 1,
            'parent_sequence_number': None,
            'md5': None,
            'sha256': None,
            'sha512': None,
            'crc32': None,
            'has_ads': False
        }
        defaults.update(kwargs)
        
        mock_record = Mock(spec=MftRecord)
        for attr, value in defaults.items():
            setattr(mock_record, attr, value)        mock_record.get_parent_record_num = Mock(return_value=defaults.get('parent_record_num', 5))
        
        return mock_record
    
    def test_sqlite_writer_initialization(self):
        """Test SQLiteWriter initialization."""
        writer = SQLiteWriter(str(self.test_db_path), self.logger)
        
        assert writer.database_path == self.test_db_path
        assert writer.logger == self.logger
        assert writer.conn is None
        assert writer.cursor is None
    
    def test_initialize_database(self):
        """Test database initialization and schema creation."""
        writer = SQLiteWriter(str(self.test_db_path), self.logger)
        writer.connect()        assert self.test_db_path.exists()
        assert writer.conn is not None
        assert writer.cursor is not None        tables = writer.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [table[0] for table in tables]
        
        expected_tables = ['mft_records', 'mft_attributes', 'attribute_types', 'file_record_flags']
        for table in expected_tables:
            assert table in table_names
    
    def test_initialize_database_already_exists(self):
        """Test initializing database when file already exists."""        writer1 = SQLiteWriter(str(self.test_db_path), self.logger)
        writer1.connect()
        writer1.close()        writer2 = SQLiteWriter(str(self.test_db_path), self.logger)
        writer2.connect()
        
        assert writer2.conn is not None
        writer2.close()
    
    def test_write_single_record(self):
        """Test writing a single MFT record."""
        writer = SQLiteWriter(str(self.test_db_path), self.logger)
        writer.connect()
        
        record = self.create_mock_record(record_num=42)
        
        writer.write_record(record, "/test/path/test_file_42.txt")
        writer.conn.commit()        result = writer.cursor.execute(
            "SELECT record_number, filename FROM mft_records WHERE record_number = ?",
            (42,)
        ).fetchone()
        
        assert result is not None
        assert result[0] == 42
        assert result[1] == 'test_file_42.txt'
        
        writer.close()
    
    def test_write_multiple_records(self):
        """Test writing multiple MFT records."""
        writer = SQLiteWriter(str(self.test_db_path), self.logger)
        writer.connect()
        
        records = [
            self.create_mock_record(record_num=i, filename=f'file_{i}.txt')
            for i in range(10)
        ]
        
        for record in records:
            writer.write_record(record, f"/test/path/file_{record.recordnum}.txt")
        
        writer.conn.commit()        count = writer.cursor.execute("SELECT COUNT(*) FROM mft_records").fetchone()[0]
        assert count == 10        for i in range(10):
            result = writer.cursor.execute(
                "SELECT filename FROM mft_records WHERE record_number = ?",
                (i,)
            ).fetchone()
            assert result[0] == f'file_{i}.txt'
        
        writer.close()
    
    def test_write_records_batch(self):
        """Test batch writing of MFT records."""
        writer = SQLiteWriter(str(self.test_db_path), self.logger)
        writer.connect()
        
        records = [
            self.create_mock_record(record_num=i)
            for i in range(100)
        ]
        
        filepaths = {i: f"/test/path/test_file_{i}.txt" for i in range(100)}
        writer.write_records_batch(records, filepaths)        count = writer.cursor.execute("SELECT COUNT(*) FROM mft_records").fetchone()[0]
        assert count == 100
        
        writer.close()
    
    def test_get_statistics(self):
        """Test statistics collection."""
        writer = SQLiteWriter(str(self.test_db_path), self.logger)
        writer.connect()        records = [
            self.create_mock_record(record_num=i, flags=1)            for i in range(5)
        ]
        records.extend([
            self.create_mock_record(record_num=i+5, flags=3)            for i in range(3)
        ])
        
        filepaths = {i: f"/test/path/test_file_{i}.txt" for i in range(8)}
        writer.write_records_batch(records, filepaths)
        
        stats = writer.get_statistics()
        
        assert 'total_records' in stats
        assert 'active_records' in stats
        assert 'directories' in stats
        assert 'deleted_records' in stats
        
        assert stats['total_records'] == 8
        
        writer.close()
    
    def test_context_manager(self):
        """Test SQLiteWriter as context manager."""
        with SQLiteWriter(str(self.test_db_path), self.logger) as writer:
            record = self.create_mock_record()
            writer.write_record(record, "/test/path/test_file_0.txt")
            
            assert writer.conn is not None    
    def test_close_without_connection(self):
        """Test closing writer without active connection."""
        writer = SQLiteWriter(str(self.test_db_path), self.logger)        writer.close()
    
    def test_commit_without_connection(self):
        """Test committing without active connection."""
        writer = SQLiteWriter(str(self.test_db_path), self.logger)        writer.close()
    
    def test_write_record_with_special_characters(self):
        """Test writing records with special characters in filenames."""
        writer = SQLiteWriter(str(self.test_db_path), self.logger)
        writer.connect()
        
        special_names = [
            "file with spaces.txt",
            "file'with'quotes.txt",
            "file\"with\"double\"quotes.txt",
            "file;with;semicolons.txt",
            "file\nwith\nnewlines.txt",
            "файл_с_unicode.txt",
            "file🌟with🌟emoji.txt"
        ]
        
        for i, filename in enumerate(special_names):
            record = self.create_mock_record(record_num=i, filename=filename)
            writer.write_record(record, f"/test/path/{filename}")
        
        writer.conn.commit()        for i, expected_filename in enumerate(special_names):
            result = writer.cursor.execute(
                "SELECT filename FROM mft_records WHERE record_number = ?",
                (i,)
            ).fetchone()
            assert result[0] == expected_filename
        
        writer.close()
    
    def test_write_record_with_null_values(self):
        """Test writing records with None/null values."""
        writer = SQLiteWriter(str(self.test_db_path), self.logger)
        writer.connect()
        
        record = self.create_mock_record(
            record_num=1,
            filename=None,
            filepath=None,
            notes=None
        )
        
        writer.write_record(record, "")
        writer.conn.commit()        result = writer.cursor.execute(
            "SELECT record_number FROM mft_records WHERE record_number = ?",
            (1,)
        ).fetchone()
        assert result is not None
        
        writer.close()
    
    def test_database_schema_integrity(self):
        """Test that database schema matches expectations."""
        writer = SQLiteWriter(str(self.test_db_path), self.logger)
        writer.connect()        schema_info = writer.cursor.execute(
            "PRAGMA table_info(mft_records)"
        ).fetchall()
        
        column_names = [col[1] for col in schema_info]
        
        expected_columns = [
            'record_number', 'filename', 'filepath',
            'flags', 'parent_record_number'
        ]
        
        for col in expected_columns:
            assert col in column_names, f"Missing column: {col}"
        
        writer.close()
    
    def test_error_handling_invalid_path(self):
        """Test error handling for invalid database path."""
        invalid_path = "/invalid/path/that/does/not/exist/test.db"
        
        with pytest.raises(Exception):
            writer = SQLiteWriter(invalid_path, self.logger)
            writer.connect()
    
    def test_concurrent_access_handling(self):
        """Test handling of concurrent database access."""        writer1 = SQLiteWriter(str(self.test_db_path), self.logger)
        writer1.connect()        record1 = self.create_mock_record(record_num=1)
        writer1.write_record(record1, "/test/path/test_file_1.txt")
        writer1.conn.commit()
        writer1.close()        writer2 = SQLiteWriter(str(self.test_db_path), self.logger)
        writer2.connect()        record2 = self.create_mock_record(record_num=2)
        writer2.write_record(record2, "/test/path/test_file_2.txt")
        writer2.conn.commit()        writer2.cursor.execute("SELECT COUNT(*) FROM mft_records")
        count = writer2.cursor.fetchone()[0]
        assert count == 2
        
        writer2.close()