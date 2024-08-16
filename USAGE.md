# AnalyzeMFT Usage Guide

This document provides detailed information on how to use the AnalyzeMFT script.

## Command-line Options

```
Usage: analyzeMFT.py [options] filename

Options:
  -h, --help            show this help message and exit
  -f FILE, --file=FILE  Read MFT from FILE
  -a, --anomaly         Turn on anomaly detection
  -l, --localtz         Report times using local timezone
  -d, --debug           Turn on debugging output
  -v, --version         Report version and exit

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
## Basic Usage

To analyze an MFT file and output the results to a CSV file:

`python AnalyzeMFT.py -f /path/to/mft_file -o /path/to/output.csv`

## Advanced Usage

1. Generate a bodyfile with standard info timestamps:

`python AnalyzeMFT.py -f /path/to/mft_file -b /path/to/bodyfile.txt --bodystd`

2. Create a CSV timeline with local timezone:

`python AnalyzeMFT.py -f /path/to/mft_file -c /path/to/timeline.csv -l`

3. Analyze MFT with anomaly detection and debugging output:

`python AnalyzeMFT.py -f /path/to/mft_file -o /path/to/output.csv -a -d`

4. Analyze an MFT file and output to CSV, bodyfile, and timeline:

`python AnalyzeMFT.py -f /path/to/mft_file -o /path/to/output.csv -b /path/to/bodyfile.txt -c /path/to/timeline.csv`

## Output Formats

1. CSV: Contains detailed information about each MFT record.
2. Bodyfile: A format suitable for timeline analysis tools.
3. CSV Timeline: A chronological representation of file system events.

## Notes

- Ensure you have the necessary permissions to read the MFT file.
- Large MFT files may take some time to process.
- Use the debugging option (-d) for troubleshooting or to get more detailed information about the parsing process.

For more information or support, please refer to the project's documentation or open an issue on the project's repository.