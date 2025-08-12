# AnalyzeMFT

AnalyzeMFT is a comprehensive Python tool for parsing and analyzing NTFS Master File Table (MFT) files. It converts binary MFT data into human-readable formats suitable for digital forensics investigations, file system analysis, and incident response activities.

## Project Synopsis

This tool provides forensic analysts and security professionals with the ability to extract detailed file system metadata from NTFS volumes. AnalyzeMFT supports multiple output formats, configurable analysis profiles, and advanced features including hash computation, chunked processing for large files, and comprehensive timeline analysis.

The project has evolved from a simple MFT parser into a full-featured forensic analysis platform with SQLite database integration, multiprocessing support, and extensive export capabilities.

## Features

### Core Analysis
- Parse NTFS MFT files of any size
- Extract file metadata, timestamps, and attributes
- Support for all standard NTFS attribute types
- Comprehensive record parsing with error handling

### Export Formats
- CSV (Comma Separated Values)
- JSON (JavaScript Object Notation)
- XML (eXtensible Markup Language)
- SQLite database with relational schema
- Excel spreadsheets (.xlsx)
- Body file format (for mactime)
- TSK timeline format
- Log2timeline CSV format

### Performance Features
- Streaming/chunked processing for large MFT files
- Multiprocessing support for hash computation
- Configurable chunk sizes for memory optimization
- Progress tracking for long-running operations

### Analysis Profiles
- **Default**: Standard analysis suitable for most use cases
- **Quick**: Minimal processing for rapid triage
- **Forensic**: Comprehensive analysis with all metadata
- **Performance**: Optimized settings for large MFT files

### Advanced Features
- Hash computation (MD5, SHA256, SHA512, CRC32)
- Configuration file support (JSON/YAML)
- Test MFT generation for development and training
- Extensible plugin architecture
- Cross-platform compatibility

## Requirements

- Python 3.8 or higher
- Required dependencies listed in requirements.txt
- Optional: PyYAML for YAML configuration support

## Installation

### From Source
```bash
git clone https://github.com/rowingdude/analyzeMFT.git
cd analyzeMFT
pip install -e .
```

### Dependencies
Install required dependencies:
```bash
pip install -r requirements.txt
```

Optional dependencies:
```bash
pip install PyYAML  # For YAML configuration support
```

## Usage

### Basic Usage
```bash
# Analyze MFT and export to CSV
python analyzeMFT.py -f /path/to/MFT -o output.csv

# Export to SQLite database
python analyzeMFT.py -f /path/to/MFT -o database.db --sqlite

# Use forensic analysis profile
python analyzeMFT.py -f /path/to/MFT -o output.csv --profile forensic

# Compute file hashes during analysis
python analyzeMFT.py -f /path/to/MFT -o output.csv --hash
```

### Advanced Usage
```bash
# Use configuration file
python analyzeMFT.py -f /path/to/MFT -o output.csv --config config.json

# Process large files with custom chunk size
python analyzeMFT.py -f /path/to/MFT -o output.csv --chunk-size 500

# Generate test MFT for development
python analyzeMFT.py --generate-test-mft test.mft --test-records 1000

# List available analysis profiles
python analyzeMFT.py --list-profiles
```

### Command Line Options
```
Usage: analyzeMFT.py -f <mft_file> -o <output_file> [options]

Export Options:
  --csv               Export as CSV (default)
  --json              Export as JSON
  --xml               Export as XML
  --excel             Export as Excel
  --body              Export as body file (for mactime)
  --timeline          Export as TSK timeline
  --sqlite            Export as SQLite database
  --tsk               Export as TSK bodyfile format

Performance Options:
  --chunk-size=SIZE   Number of records per chunk (default: 1000)
  -H, --hash          Compute hashes (MD5, SHA256, SHA512, CRC32)
  --no-multiprocessing-hashes
                      Disable multiprocessing for hash computation
  --hash-processes=N  Number of hash computation processes

Configuration Options:
  -c FILE, --config=FILE
                      Load configuration from JSON/YAML file
  --profile=NAME      Use analysis profile (default, quick, forensic, performance)
  --list-profiles     List available analysis profiles
  --create-config=FILE
                      Create sample configuration file

Verbosity Options:
  -v                  Increase output verbosity
  -d                  Increase debug output
```

## Output Example

```
Starting MFT analysis...
Processing MFT file: /evidence/MFT
Using chunk size: 1000 records
MFT file size: 83,886,080 bytes, estimated 81,920 records
Processed 10000 records...
Processed 20000 records...
MFT processing complete. Total records processed: 81,920
Writing output in csv format to analysis_results.csv
Analysis complete.

MFT Analysis Statistics:
Total records processed: 81,920
Active records: 45,231
Directories: 12,847
Files: 69,073
Unique MD5 hashes: 31,256
Analysis complete. Results written to analysis_results.csv
```

## Upcoming Features

The following enhancements are planned for future releases:

### Performance & Scalability
- Parallel processing for record parsing
- Progress bars with ETA calculations
- Enhanced memory optimization

### Analysis Features
- Anomaly detection for timeline gaps
- Suspicious file size detection
- Parent-child directory tree mapping
- Orphaned file detection
- Timestamp comparison analysis

### User Experience
- Date range filtering
- File type and size filtering
- Interactive web interface
- Enhanced CLI with auto-completion

### Export & Integration
- STIX/TAXII format support
- Elasticsearch/Splunk integration
- Neo4j graph database export
- Custom field selection

## Contributing

Contributions are welcome and encouraged. To contribute:

### Requirements for Contributions
- Python 3.8+ compatibility
- Comprehensive unit tests for new features
- Type hints for all new code
- Documentation for new functionality
- Cross-platform compatibility (Windows, Linux, macOS)

### Development Setup
```bash
git clone https://github.com/rowingdude/analyzeMFT.git
cd analyzeMFT
pip install -e .
pip install -r requirements-dev.txt
```

### Testing
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Code Quality
- Follow PEP 8 style guidelines
- Use type hints throughout
- Maintain test coverage above 80%
- Document all public APIs

### Submitting Changes
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all tests pass
5. Submit a pull request

## Version

Current version: 3.1.0

## Author

Benjamin Cance (bjc@tdx.li)

## License

Copyright Benjamin Cance 2024

Licensed under the MIT License. See LICENSE.txt for details.

## Disclaimer

This tool is provided as-is for legitimate forensic and security analysis purposes. Users are responsible for ensuring they have proper authorization before analyzing any file systems or MFT data. The authors assume no liability for misuse of this software.
