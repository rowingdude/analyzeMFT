#!/usr/bin/env python3

import pytest
import json
import tempfile
import os
from pathlib import Path
from dataclasses import asdict
from src.analyzeMFT.config import ConfigManager, AnalysisProfile


class TestAnalysisProfile:
    """Test AnalysisProfile class functionality."""
    
    def test_profile_initialization_defaults(self):
        """Test AnalysisProfile initialization with default values."""
        profile = AnalysisProfile()
        assert profile.name == "default"
        assert profile.description == "Default analysis profile"
        assert profile.export_format == "csv"
        assert profile.compute_hashes is False
        assert profile.verbosity == 0
        assert profile.debug == 0
        assert profile.chunk_size == 1000
    
    def test_profile_initialization_custom(self):
        """Test AnalysisProfile initialization with custom values."""
        profile = AnalysisProfile(
            name="forensic",
            description="Comprehensive forensic analysis",
            export_format="sqlite",
            compute_hashes=True,
            verbosity=2,
            debug=1,
            chunk_size=500
        )
        assert profile.name == "forensic"
        assert profile.description == "Comprehensive forensic analysis"
        assert profile.export_format == "sqlite"
        assert profile.compute_hashes is True
        assert profile.verbosity == 2
        assert profile.debug == 1
        assert profile.chunk_size == 500
    
    def test_profile_to_dict_via_asdict(self):
        """Test AnalysisProfile serialization to dictionary using asdict."""
        profile = AnalysisProfile(
            name="test_profile",
            export_format="json",
            compute_hashes=True
        )
        result = asdict(profile)
        
        assert isinstance(result, dict)
        assert result["name"] == "test_profile"
        assert result["export_format"] == "json"
        assert result["compute_hashes"] is True
    
    def test_profile_dataclass_fields(self):
        """Test that AnalysisProfile has expected dataclass fields."""
        profile = AnalysisProfile()        expected_fields = [
            'name', 'description', 'export_format', 'compute_hashes',
            'verbosity', 'debug', 'chunk_size', 'enable_anomaly_detection',
            'file_size_threshold_mb', 'date_filter_start', 'date_filter_end',
            'file_types_include', 'file_types_exclude', 'min_file_size',
            'max_file_size', 'include_deleted', 'include_system_files',
            'custom_fields'
        ]
        
        for field in expected_fields:
            assert hasattr(profile, field), f"Missing field: {field}"


class TestConfigManager:
    """Test ConfigManager class functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.config_manager = ConfigManager()
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_config_manager_initialization(self):
        """Test ConfigManager initialization."""
        cm = ConfigManager()
        assert hasattr(cm, 'profiles')
        assert isinstance(cm.profiles, dict)
        assert len(cm.profiles) > 0    
    def test_list_profiles(self):
        """Test listing available profiles."""
        profiles = self.config_manager.list_profiles()
        assert isinstance(profiles, dict)
        assert "default" in profiles
        assert "quick" in profiles
        assert "forensic" in profiles
        assert "performance" in profiles        for name, description in profiles.items():
            assert isinstance(name, str)
            assert isinstance(description, str)
            assert len(description) > 0
    
    def test_get_profile_default(self):
        """Test getting the default profile."""
        profile = self.config_manager.get_profile("default")
        assert profile is not None
        assert isinstance(profile, AnalysisProfile)
        assert profile.name == "default"
    
    def test_get_profile_forensic(self):
        """Test getting the forensic profile."""
        profile = self.config_manager.get_profile("forensic")
        assert profile is not None
        assert isinstance(profile, AnalysisProfile)
        assert profile.name == "forensic"
        assert profile.compute_hashes is True    
    def test_get_profile_performance(self):
        """Test getting the performance profile."""
        profile = self.config_manager.get_profile("performance")
        assert profile is not None
        assert isinstance(profile, AnalysisProfile)
        assert profile.name == "performance"
        assert profile.chunk_size > 1000    
    def test_get_profile_nonexistent(self):
        """Test getting a non-existent profile."""
        profile = self.config_manager.get_profile("nonexistent")
        assert profile is None
    
    def test_create_sample_config_json(self):
        """Test creating a sample JSON configuration file."""
        config_path = Path(self.temp_dir) / "test_config.json"
        
        self.config_manager.create_sample_config(config_path)
        
        assert config_path.exists()        with open(config_path, 'r') as f:
            config_data = json.load(f)        assert "name" in config_data
        assert "export_format" in config_data
        assert "compute_hashes" in config_data
        assert isinstance(config_data, dict)
    
    def test_create_sample_config_yaml(self):
        """Test creating a sample YAML configuration file."""
        config_path = Path(self.temp_dir) / "test_config.yaml"
        
        try:
            self.config_manager.create_sample_config(config_path)
            assert config_path.exists()            try:
                import yaml
                with open(config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                assert "name" in config_data
            except ImportError:                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                assert "name" in config_data
                
        except Exception as e:            assert "YAML" in str(e) or "yaml" in str(e)
    
    def test_load_config_file_json(self):
        """Test loading configuration from JSON file."""
        config_data = {
            "name": "test_profile",
            "description": "Test configuration profile",
            "export_format": "sqlite",
            "compute_hashes": True,
            "verbosity": 2,
            "debug": 1,
            "chunk_size": 750
        }
        
        config_path = Path(self.temp_dir) / "test_load.json"
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        loaded_config = self.config_manager.load_config_file(config_path)
        
        assert isinstance(loaded_config, dict)
        assert loaded_config["name"] == "test_profile"
        assert loaded_config["export_format"] == "sqlite"
        assert loaded_config["compute_hashes"] is True
    
    def test_load_profile_from_config(self):
        """Test loading a profile from configuration data."""
        config_data = {
            "name": "loaded_profile",
            "description": "Profile loaded from config",
            "export_format": "xml",
            "compute_hashes": False,
            "verbosity": 1,
            "debug": 0,
            "chunk_size": 2000
        }
        
        profile = self.config_manager.load_profile_from_config(config_data, "loaded_profile")
        
        assert profile is not None
        assert isinstance(profile, AnalysisProfile)
        assert profile.name == "loaded_profile"
        assert profile.export_format == "xml"
        assert profile.chunk_size == 2000
    
    def test_save_profile(self):
        """Test saving a profile to configuration file."""
        config_path = Path(self.temp_dir) / "saved_profile.json"
        
        profile = AnalysisProfile(
            name="saved_test",
            description="Test saved profile",
            export_format="json",
            compute_hashes=True,
            chunk_size=1500
        )
        
        self.config_manager.save_profile(profile, config_path)
        
        assert config_path.exists()        with open(config_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["name"] == "saved_test"
        assert saved_data["export_format"] == "json"
        assert saved_data["compute_hashes"] is True
        assert saved_data["chunk_size"] == 1500
    
    def test_load_config_file_invalid_path(self):
        """Test loading configuration from non-existent file."""
        with pytest.raises(FileNotFoundError):
            self.config_manager.load_config_file("/nonexistent/path/config.json")
    
    def test_load_config_file_invalid_json(self):
        """Test loading configuration from invalid JSON file."""
        config_path = Path(self.temp_dir) / "invalid.json"
        with open(config_path, 'w') as f:
            f.write("{ invalid json content")
        
        with pytest.raises(json.JSONDecodeError):
            self.config_manager.load_config_file(config_path)
    
    def test_default_profiles_structure(self):
        """Test that default profiles have expected structure."""
        expected_profiles = ["default", "quick", "forensic", "performance"]
        
        for profile_name in expected_profiles:
            profile = self.config_manager.get_profile(profile_name)
            assert profile is not None
            assert profile.name == profile_name
            assert isinstance(profile.description, str)
            assert len(profile.description) > 0
    
    def test_forensic_profile_settings(self):
        """Test forensic profile has appropriate settings."""
        profile = self.config_manager.get_profile("forensic")
        
        assert profile.compute_hashes is True
        assert profile.enable_anomaly_detection is True
        assert profile.include_deleted is True
        assert profile.include_system_files is True
        assert profile.verbosity >= 1
    
    def test_quick_profile_settings(self):
        """Test quick profile has appropriate settings."""
        profile = self.config_manager.get_profile("quick")
        
        assert profile.compute_hashes is False
        assert profile.include_deleted is False
        assert profile.chunk_size >= 1000    
    def test_performance_profile_settings(self):
        """Test performance profile has appropriate settings."""
        profile = self.config_manager.get_profile("performance")
        
        assert profile.export_format == "sqlite"        assert profile.chunk_size >= 1000        assert profile.include_deleted is False        assert profile.include_system_files is False  # Skip system files for performance