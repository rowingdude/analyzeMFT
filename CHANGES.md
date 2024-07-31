# Changelog

## [Unreleased]
- Created a testing branch:
-- This branch is the basis for a (almost) complete rewrite. When it's finished, the current branch here will be archived.
-- There will be GUI additions called analyzeMFT-gtk and analyzeMFT-qt
-- It would be nice to see an ncurses also

- All of the standing issues will be considered and worked through the new re-write.

## [4.0.1] - 2024-07-31
- Fixed a two's complement error in the bitparse.py

## [4.0.0] - 2024-04-29
- New maintainer.
- Reworked older Python code to adhere to new PEPs.
- Added type hinting.

## [3.0.1] - 2022-09-07
- Completed Python 3 update.
- Fixed Unicode-related issues.
- Updated shebangs and other Python 3 related changes.

## [3.0.0] - 2019-07-19
- Updated to Python 3.

## [2.0.19] - 2016-11-30
- Changed `objectID` parsing to translate the first 8 bytes to little endian.
- General code cleanup.

## [2.0.19] - 2016-05-27
- Properly handled `fncnt` findings > 3.
- Allowed user to use either Windows or Unix path separators.

## [2.0.18] - 2015-05-24
- Versioning hack.

## [2.0.17] - 2015-05-23
- Versioning hack.

## [2.0.16] - 2015-05-21
- Documentation fixes.
- Attribute fixes based on NTFS version.

## [2.0.15] - 2015-02-08
- Fixed 2's complement computation.
- Reintroduced anomaly detection.

## [2.0.14] - 2014-11-24
- Fixed directory structure issues.

## [2.0.12] - 2014-03-15
- Added `-e`, `--excel` switch to format date/times for proper Excel import.

## [2.0.11] - 2013-08-07
- Improved filename reporting to favor non-8.3 format when available.

## [2.0.10] - 2013-08-02
- Added additional datarun support.

## [2.0.09] - 2013-08-02
- Further enhancements to datarun support.

## [2.0.08] - 2013-08-02
- Initial datarun support added.

## [2.0.07] - 2013-07-21
- Fixed parsing and printing of UTF-16 strings.
- Added support for Alternate Data Streams (ADS).
- Updated ADS records to include a new ADS column.

## [2.0.07] - 2013-07-19
- Fixed incorrect value readings.

## [2.0.06] - 2013-07-17
- Fixed bug in ATR processing.

## [2.0.05] - 2013-07-14
- Added `-s` switch for small memory systems.
- Added `-p` switch to show progress.

## [2.0.04] - 2013-07-xx
- Minor tweaks to support external programs.

## [2.0.03] - 2013-06-xx
- Restructured to support PyPi (pip).

## [2.0.02] - 2013-06-24
- OOP refactor and partial de-OOP to address memory issues.
- Setup for PyPi (pip).

## [1.16] - 2013-05-17
- Restructured layout in preparation for module creation.

