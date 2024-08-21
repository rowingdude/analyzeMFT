# AnalyzeMFT

AnalyzeMFT is a Python script designed to translate the NTFS Master File Table (MFT) into a human-readable and searchable format, such as CSV. This tool is useful for digital forensics, file system analysis, and understanding the structure of NTFS volumes.

## Features

- Parse NTFS MFT files
- Generate CSV output of MFT records
- Create timeline in CSV format
- Produce bodyfile output for timeline analysis
- Support for local timezone reporting
- Anomaly detection (optional)
- Debugging output (optional)

## Requirements

- Python 3.x

## Installation

1. Clone this repository or download the script files.
2. Ensure you have Python 3.x installed on your system.

Basic usage:

`python AnalyzeMFT.py -f <mft_file> -o <output_file>`

## Versioning

Current version: 3.0

## Author

Benjamin Cance (bjc@tdx.li)

## License

Copyright Benjamin Cance 2024

## Contributing

If you'd like to contribute to this project, please submit a pull request or open an issue on the project's repository.

## Disclaimer

This tool is provided as-is, without any warranties. Use at your own risk and ensure you have the necessary permissions before analyzing any file systems or MFT data.

