# AnalyzeMFT

AnalyzeMFT is a Python script designed to translate the NTFS Master File Table (MFT) into a human-readable and searchable format, such as CSV. This tool is useful for digital forensics, file system analysis, and understanding the structure of NTFS volumes.

## AnalyzeMFT Derivatives

Rather than clutter up the main project with features people may not want, I will be releasing two sister projects this week:

1. AnalyzeMFT-SQLite which adds SQL tables as an export option. I found that when working with very large MFT files, it's often easier to get them into a database such as SQLite or PostgreSQL and perform queries/searches using those tools. This also lets us cut down on the total size of the eventual export with large MFT files because we can reuse values and attributes.

2. CanalyzeMFT - This is a C/C++ port of the project. The goal is to increase the performance on *nix systems (or Windows if you want to build it there). I'm aiming to leave out system dependent libraries (cough Windows.h) so it's easily built everywhere. 

## Features

- Parse NTFS MFT files
- Generate CSV output of MFT records
- Create timeline in CSV format
- Produce bodyfile output for timeline analysis
- Support for local timezone reporting
- Many output formats - CSV, Body Files, JSON
- Anomaly detection (optional)
- Debugging output (optional)

## Requirements

- Python 3.x

## Installation

1. Clone this repository or download the script files.
2. Ensure you have Python 3.x installed on your system.

Basic usage:

```
Usage: analyzeMFT.py [options] filename

Options:
  -h, --help            show this help message and exit
  -f FILE, --file=FILE  Read MFT from FILE
  -a, --anomaly         Turn on anomaly detection
  -l, --localtz         Report times using local timezone
  -d, --debug           Turn on debugging output
  -v, --version         Report version and exit
  -V, --verbose         Provide additional output as the program runs (Dangerous, can produce a lot of information)

  Output Options:
    -o FILE, --output=FILE
                        Write results to CSV FILE
    -b FILE, --bodyfile=FILE
                        Write MAC information to bodyfile
    -c FILE, --csvtimefile=FILE
                        Write CSV format timeline file

  Body File Options:
    --bodystd           Use STD_INFO timestamps for body file rather than FN     
                        timestamps
    --bodyfull          Use full path name + filename rather than just
                        filename

  Performance Options:
    --threads=THREAD_COUNT
                        Number of threads to use for parsing (default: 1)
```

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

