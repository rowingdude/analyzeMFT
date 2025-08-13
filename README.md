# AnalyzeMFT

![Tests](https://github.com/rowingdude/analyzeMFT/workflows/Test%20Suite/badge.svg)
![CI/CD](https://github.com/rowingdude/analyzeMFT/workflows/CI%2FCD%20Pipeline/badge.svg)
[![codecov](https://codecov.io/gh/rowingdude/analyzeMFT/branch/master/graph/badge.svg)](https://codecov.io/gh/rowingdude/analyzeMFT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

### Brief Introduction
**AnalyzeMFT** is a Python-based tool designed for parsing and analyzing the NTFS Master File Table (MFT). 

It transforms raw binary MFT data into structured, human-readable output suitable for digital forensics, incident response, and file system analysis. The tool supports a wide range of output formats and provides detailed metadata extraction, enabling investigators to examine file timestamps, attributes, and structural properties of NTFS volumes. 

The primary purpose of AnalyzeMFT is to assist forensic analysts in reconstructing file system activity by decoding MFT records. Each record contains critical information such as file names, creation and modification times, file sizes, and directory relationships. The tool handles both active and deleted entries, allowing for comprehensive timeline analysis and artifact recovery. It includes robust error handling to manage corrupted or incomplete MFT entries, ensuring reliable processing even on damaged file systems. 

### Outputs
Multiple output formats are supported to integrate with common forensic workflows. Users can export results as CSV, JSON, XML, or Excel files for review and reporting. For timeline analysis, the body file format compatible with mactime and other tools is available. SQLite export creates a relational database structure for querying and long-term storage. The TSK timeline and log2timeline CSV formats allow direct ingestion into established forensic platforms. 

### Optimization
Performance optimizations are built into the tool to handle large MFT files efficiently. Processing occurs in configurable chunks to manage memory usage, particularly important when analyzing MFTs that are hundreds of megabytes in size. Multiprocessing is used during hash computation to reduce processing time. Users can adjust the number of worker processes and chunk size based on system resources. Progress indicators provide real-time feedback during long-running operations. 

### Features
The tool supports configurable analysis profiles to suit different operational needs. The default profile provides balanced processing for general use. The quick profile minimizes processing overhead for rapid triage. The forensic profile enables maximum data extraction, including all timestamp variants and extended attributes. The performance profile adjusts internal settings to prioritize speed and resource efficiency on large datasets. 

Hash computation is available for file record attributes that include data runs. MD5, SHA256, SHA512, and CRC32 hashes can be generated for resident and non-resident data. This feature supports file identification and integrity verification. Hashing runs in parallel by default, with the number of processes configurable. Users can disable multiprocessing if running in constrained environments. 

Configuration is managed through command-line options or external files in JSON or YAML format. A configuration file can define output settings, analysis profiles, hash options, and filtering criteria. Sample configuration files can be generated using the --create-config option. The --list-profiles option displays all available built-in profiles and their descriptions. 

Input is specified using the -f option followed by the path to the MFT file. Output format is determined by the file extension or explicit export flags. The -o option sets the output destination. When exporting to SQLite, the --sqlite flag must be used. For CSV output, no additional flag is required if the output file ends in .csv. 

A test MFT generator is included for development and training purposes. Using the --generate-test-mft option, users can create synthetic MFT files with a specified number of records. This feature is useful for validating tool functionality, testing parsers, or creating demonstration data. 

Command-line options include verbosity controls with -v for increased output and -d for debug-level logging. These help diagnose issues during processing. Export options allow selection of format without relying on file extensions. Performance tuning options include --chunk-size for record batch size and --hash-processes to set the number of hashing threads. 

The tool includes a structured help system. Running the script with --help displays all available options and their descriptions. The usage summary shows required and optional arguments. Detailed explanations are provided for each category of options, including export, performance, configuration, and debugging settings. 

### Development
Version 3.1.0 includes significant improvements to code quality and test coverage. The test suite now includes 224 comprehensive tests covering all major components. GitHub Actions CI/CD pipelines ensure code quality across Python 3.8-3.12 on Linux, Windows, and macOS. Security scanning with Bandit and dependency checking with Safety are integrated into the build process. Code coverage reporting through Codecov tracks test effectiveness. 

Planned export formats include STIX/TAXII for threat intelligence sharing, and integration with Elasticsearch and Splunk for centralized log analysis. Graph database export to Neo4j will enable visualization of file system relationships. Users will be able to filter output by date range, file type, and size directly within the tool. An interactive mode may be introduced to allow step-by-step examination of records. 

Contributions to the project are accepted via GitHub pull requests. Developers must ensure compatibility with Python 3.8 and above. All new code must include type hints and comprehensive unit tests. The test suite is run using pytest, and coverage must remain above 80%. Code should follow PEP 8 guidelines and be cross-platform compatible. Documentation must be updated for any new features or changes. 

## Disclaimer

This tool is provided as-is for legitimate forensic and security analysis purposes. Users are responsible for ensuring they have proper authorization before analyzing any file systems or MFT data. The authors assume no liability for misuse of this software.
