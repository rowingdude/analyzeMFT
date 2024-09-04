
## Version 3.0.5

### Fixes

- Fixed a CSV writer initialization error (that I caused) when migration functionality to File_Writer.py
- Fixed a typo where we weren't correctly parsing Object IDs

### Changes

- Added verbosity options for output, `-v` works and so does `-vv`, `-d` works similarly.
- Introduced the concept of a testing framework in the testing/ folder. Please see `requirements-dev.txt` if you'd like to run those.
- In the testing framework, I copied/pasted the bulk of Constants.py and started to make tests for each item

### Upcoming

-  _Fix the root path file name_
- Still need to better utilize Python3 conventions
- I Can haz Database?!





## Versions 3.0.2 and 3.0.3 

### Changes
- Brought back XML, JSON outputs
- Added optional Excel output (requires openpyxl)
- Restored type hints
- Tinkered a little more with the attribute specific functions

### Fixes
- Fixed a minor CSV formatting error where path names weren't being correctly parsed.

### To do
- Fix the root path file name - currently the parser picks up everything after the `C:\`, I'd like to have the target drive letter also
- Add verbose and very verbose output to accompany debug
- Create tests for each class, module, and output type.
- Finish migrating the `MFTRecord.To_CSV()` functionality to `FileWriters.WriteCSV()` 
   - Should I be making a new module called `Output_Format`, thus invoking items like `Output_Format.TO_CSV()` .. seems like a lot of work for marginal gain.
- Better utilize Python built-ins like `@dataclass` and `@staticmethod` on items that would be equivalent to C's `enums` and `structs`.
- Sort out the documentation and steps to implement a SQLite or PostgreSQL database and use that as an output format. 

### Big thanks!
To my wife, Jessica, for giving me the motivation to pick this project back up and get it back to a stable, working state. Also thank you to the Reddit Arduino community for helping me consolidate my thoughts on this and some other projects.

## Version 3.0.1 (2024-09-03)

### Changes
- Implementing asyncio for improved performance and responsiveness.
- Handles potential issues with asyncio on different platforms, especially Windows.
- Added the ability to compute and include various hash types (MD5, SHA256, SHA512, CRC32) optionally.

### Fixes
- Now uses a more robust method to build file paths, handling edge cases like root directory and orphaned files.
- Set all relevant data, including optional hash information, to be correctly written to the CSV file.

### Upcoming additions:

- Granular processing of each attribute type, file type, etc found in Constants.py (3.0.2)
- Readmission of file export types other than CSV - XML, JSON, Excel, etc. (3.0.3)
- Readmission of forensic file types such as the Body file (3.0.4)
- Optional integration of SQLite (3.0.5)
- Optional user stipulated fields and reordering of the CSV with optional header (3.0.6)



## Version 3.0 (2024-08-15)

Work has completed on the class-based layout. The program has been split into individual files each composed of the class within. 
I believe this is the way to go (personal preference) as I like to work on one module at a time!



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

