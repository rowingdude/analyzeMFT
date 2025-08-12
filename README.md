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
The project has undergone significant improvements in version 3.1.0. All syntax errors in the main entry point and test files have been resolved. The test suite now includes 160 passing tests with comprehensive coverage of core functionality. Dependencies have been updated and documented in requirements.txt to include pytest, pytest-asyncio, and PyYAML for testing and configuration support. Version numbering has been standardized across all project files.

Code quality improvements include enhanced error handling in the hash processor for systems where CPU count detection fails. The MFT record parser now validates record sizes and handles incomplete records gracefully. Configuration management supports both JSON and YAML formats with automatic fallback when PyYAML is unavailable. Integration tests have been updated to work with the current test MFT generator implementation.

The testing infrastructure is now fully operational with all tests passing when pytest is installed. Async tests require pytest-asyncio but the core application functions without it. Test data generation has been corrected to use proper struct packing formats. Path resolution in tests now handles both relative and absolute paths correctly. The project maintains Python 3.7+ compatibility as specified in setup.py. 

## Disclaimer

This tool is provided as-is for legitimate forensic and security analysis purposes. Users are responsible for ensuring they have proper authorization before analyzing any file systems or MFT data. The authors assume no liability for misuse of this software.
