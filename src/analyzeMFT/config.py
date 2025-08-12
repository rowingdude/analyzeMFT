import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from .validators import validate_config_schema, ConfigValidationError

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

@dataclass
class AnalysisProfile:
    name: str = "default"
    description: str = "Default analysis profile"
    export_format: str = "csv"
    compute_hashes: bool = False
    verbosity: int = 0
    debug: int = 0
    chunk_size: int = 1000
    enable_anomaly_detection: bool = False
    file_size_threshold_mb: int = 100
    date_filter_start: Optional[str] = None
    date_filter_end: Optional[str] = None
    file_types_include: Optional[list] = None
    file_types_exclude: Optional[list] = None
    min_file_size: Optional[int] = None
    max_file_size: Optional[int] = None
    include_deleted: bool = True
    include_system_files: bool = True
    custom_fields: Optional[list] = None

class ConfigManager:
    
    def __init__(self):
        self.logger = logging.getLogger('analyzeMFT.config')
        self.config_dir = self._get_config_dir()
        self.profiles: Dict[str, AnalysisProfile] = {}
        self._load_default_profiles()
    
    def _get_config_dir(self) -> Path:
        home_config = Path.home() / '.analyzeMFT'
        if home_config.exists() or not home_config.parent.exists():
            return home_config
        return Path.cwd() / '.analyzeMFT'
    
    def _load_default_profiles(self) -> None:
        self.profiles['default'] = AnalysisProfile()
        self.profiles['quick'] = AnalysisProfile(
            name="quick",
            description="Quick analysis with minimal output",
            export_format="csv",
            compute_hashes=False,
            verbosity=0,
            chunk_size=5000,
            include_deleted=False
        )
        self.profiles['forensic'] = AnalysisProfile(
            name="forensic",
            description="Comprehensive forensic analysis",
            export_format="csv",
            compute_hashes=True,
            verbosity=1,
            debug=1,
            enable_anomaly_detection=True,
            include_deleted=True,
            include_system_files=True
        )
        self.profiles['performance'] = AnalysisProfile(
            name="performance",
            description="Optimized for large MFT files",
            export_format="sqlite",
            compute_hashes=False,
            verbosity=1,
            chunk_size=10000,
            include_deleted=False,
            include_system_files=False
        )
    
    def load_config_file(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yml', '.yaml']:
                    if not HAS_YAML:
                        raise ImportError("PyYAML is required for YAML configuration files. Install with: pip install PyYAML")
                    config = yaml.safe_load(f)
                elif config_path.suffix.lower() == '.json':
                    config = json.load(f)
                else:
                    content = f.read()
                    f.seek(0)
                    if content.strip().startswith('{'):
                        config = json.load(f)
                    elif HAS_YAML:
                        config = yaml.safe_load(f)
                    else:
                        raise ValueError("Unable to determine configuration file format. Use .json or .yaml extension.")
            
            self.logger.info(f"Loaded configuration from {config_path}")
            return config
            
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            self.logger.error(f"Error parsing configuration file {config_path}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading configuration file {config_path}: {e}")
            raise
    
    def load_profile_from_config(self, config: Dict[str, Any], profile_name: str = "custom") -> AnalysisProfile:
        try:
            validated_config = validate_config_schema(config)
            self.logger.info(f"Configuration validation successful for profile '{profile_name}'")
        except ConfigValidationError as e:
            self.logger.error(f"Configuration validation failed for profile '{profile_name}': {e}")
            raise
        
        profile_data = asdict(self.profiles['default'])
        profile_data.update(validated_config)
        profile_data['name'] = profile_name
        
        return AnalysisProfile(**profile_data)
    
    def save_profile(self, profile: AnalysisProfile, config_path: Union[str, Path]) -> None:
        config_path = Path(config_path)
        config_data = asdict(profile)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yml', '.yaml']:
                    if not HAS_YAML:
                        raise ImportError("PyYAML is required for YAML configuration files. Install with: pip install PyYAML")
                    yaml.dump(config_data, f, default_flow_style=False, indent=2)
                else:
                    json.dump(config_data, f, indent=2)
            
            self.logger.info(f"Saved profile '{profile.name}' to {config_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving profile to {config_path}: {e}")
            raise
    
    def get_profile(self, name: str) -> Optional[AnalysisProfile]:
        return self.profiles.get(name)
    
    def list_profiles(self) -> Dict[str, str]:
        return {name: profile.description for name, profile in self.profiles.items()}
    
    def create_sample_config(self, config_path: Union[str, Path]) -> None:
        config_path = Path(config_path)
        
        sample_config = {
            "name": "default",
            "description": "Default configuration file",
            "export_format": "csv",
            "compute_hashes": False,
            "verbosity": 1,
            "debug": 0,
            "chunk_size": 1000,
            "enable_anomaly_detection": False,
            "file_size_threshold_mb": 100,
            "date_filter_start": None,
            "date_filter_end": None,
            "file_types_include": None,
            "file_types_exclude": ["$MFT", "$MFTMirr"],
            "min_file_size": None,
            "max_file_size": None,
            "include_deleted": True,
            "include_system_files": True,
            "custom_fields": None
        }
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yml', '.yaml']:
                    if not HAS_YAML:
                        json.dump(sample_config, f, indent=2)
                    else:
                        yaml.dump(sample_config, f, default_flow_style=False, indent=2)
                else:
                    json.dump(sample_config, f, indent=2)
            
            self.logger.info(f"Created sample configuration file: {config_path}")
            
        except Exception as e:
            self.logger.error(f"Error creating sample configuration file: {e}")
            raise

def get_default_config_paths() -> list:
    config_dir = Path.home() / '.analyzeMFT'
    cwd_config = Path.cwd()
    
    paths = []
    for ext in ['json', 'yaml', 'yml']:
        paths.append(config_dir / f'config.{ext}')
        paths.append(config_dir / f'analyzeMFT.{ext}')
    for ext in ['json', 'yaml', 'yml']:
        paths.append(cwd_config / f'analyzeMFT.{ext}')
        paths.append(cwd_config / f'.analyzeMFT.{ext}')
    
    return paths

def find_config_file() -> Optional[Path]:
    for path in get_default_config_paths():
        if path.exists():
            return path
    return None