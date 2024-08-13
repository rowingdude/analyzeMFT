
# AnalyzeMFT Change Log

This document lists the changes and version history for the AnalyzeMFT script and component scripts.

## Version 2.1.2 (2024-08-13)

Work has officially begun on the next minor revision of this application. The to do list is below. We'll update as things get finished.

### To do list:

1. Finish the "class based layout"
2. Improve the readabilityby breaking up some of the large functions like `parse_records`
3. Implement a testing framework involving the sister project [GenerateMFT](https://github.com/rowingdude/GenerateMFT/).
4. Implement multithreading as an option


## Version 2.1.1 (2024-08-02)

### Changes
- Updated to current PEP standards
- Improved code formatting and structure
- Enhanced type hinting for better code readability and maintainability
- Migrated v2.0.4 readme and changes files to deprecated
- Updated v2.1.0 markdown files are in main

### Fixes
- Resolved issues with Unicode handling in filenames
- Fixed potential bugs in timestamp conversions

## Version 2.0.2

### Changes
- Improved error handling for corrupt MFT records
- Enhanced support for analyzing large MFT files

### Fixes
- Resolved issues with self-referential parent sequence numbers
- Fixed bugs in folder path generation

## Version 2.0.1

### Changes
- Added support for CSV timeline output
- Implemented local timezone reporting option

### Fixes
- Corrected issues with bodyfile output formatting

## Version 2.0

### Major Changes
- Complete rewrite of the script for improved performance and maintainability
- Added support for anomaly detection
- Implemented debugging output option

### New Features
- Bodyfile output for timeline analysis
- Option to use STD_INFO or FN timestamps for bodyfile

## Version 1.0 (Initial Release)

- Basic functionality to parse NTFS MFT and output to CSV
- Support for reading MFT files and generating human-readable output

Note: Exact release dates for versions prior to 2.1 are not specified in the provided code. If you have this information, please add the specific dates to each version.


# Repository Updates:
## August 2nd, 2024:
- On 30-July-2024 it seems my automated repository management went awry. Instead of a simple push/pull to refresh the branches, I wrongly set to merge the testing branch into the master branch, causing quite a bit of chaos. The CI/CD pipeline took a hit, but we'll get things back on track. Over the past couple days, I've restored the old files and incorporated the necessary reworks. To keep things organized, I've moved the "new" materials to a dedicated "testing" folder, while the mildly updated files remain in the master branch. As an added measure, I've implemented branch protections on the master branch. From now on, every change will require a "sign off" and a pull request. Once we're back to normal operations, these protections will be strictly enforced.

