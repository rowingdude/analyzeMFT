===========
Analyze MFT
===========

analyzeMFT.py is designed to fully parse the MFT file from an NTFS filesystem
and present the results as accurately as possible in multiple formats.

Installation
===========
You should now be able to install analyzeMFT with pip:

    pip install analyzeMFT
    
Alternatively:

    git pull https://github.com/dkovar/analyzeMFT.git
    python setup.py install (or, just run it from that directory)

Usage
===========
Usage: analyzeMFT.py [options]

Options:
  -h, --help            show this help message and exit
  -v, --version         report version and exit
  
File input options:

  -f FILE, --file=FILE  read MFT from FILE

File output options:

  -o FILE, --output=FILE
                        write results to FILE
  -c FILE, --csvtimefile=FILE
                        write CSV format timeline file
  -b FILE, --bodyfile=FILE
                        write MAC information to bodyfile

Options specific to body files:

  --bodystd             Use STD_INFO timestamps for body file rather than FN
                        timestamps
  --bodyfull            Use full path name + filename rather than just
                        filename

Other options:

  -a, --anomaly         turn on anomaly detection
  -l, --localtz         report times using local timezone
  -e, --excel           print date/time in Excel friendly format
  -d, --debug           turn on debugging output
  -s, --saveinmemory    Save a copy of the decoded MFT in memory. Do not use
                        for very large MFTs
  -p, --progress        Show systematic progress reports.
  -w, --windows-path    Use windows path separator when constructing the filepath instead of linux

Output
=========

analyzeMFT can produce output in CSV or bodyfile format.

CSV output
---------
The output is currently written in CSV format. Due to the fact that Excel
automatically determines the type of data in a column, it is recommended that
you write the output to a file without the .csv extension, open it in Excel, and
set all the columns to "Text" rather than "General" when the import wizard
starts. Failure to do so will result in Excel formatting the columns in a way
that misrepresents the data.

I could pad the data in such a way that forces Excel to set the column type correctly
but this might break other tools.

GUI:
You can turn off all the GUI dependencies by setting the noGUI flag to 'True'. This is for installations that don't want to install the tk/tcl libraries.

Update History
=============
[See CHANGES.txt]

Version 2.0.4:Minor tweaks to support external programs
Version 2.0.3:Restructured to support PyPi (pip)
Version 2.0.2:De-OOP'd MFT record parsing to reduce memory consumption
Version 2.0.1:Added L2T CSV and body file support back in, fixed some minor bugs along the way
              Made full file path calculation more efficient
Version 2.0.0 Restructured layout to turn it into a module.
              Made it more OOP.
              Improved error handling and corrupt record detection
              
------ Version 1 history follows ------

Version 1.0: Initial release
Version 1.1: Split parent folder reference and sequence into two fields. I'm still trying to figure out the
             significance of the parent folder sequence number, but I'm convinced that what some documentation
             refers to as the parent folder record number is really two values - the parent folder record number
             and the parent folder sequence number.
Version 1.2: Fixed problem with non-printable characters in filenames. Any Unicode character is legal in a
             filename, including newlines. This presented some problems in my output. Characters that do not
             render well are now converted to hex and a note is added to the Notes column indicating this.
             (I've learned a lot about Unicode since I first wrote this.)
             Added "compile time" flag to turn off the inclusion of any GUI related modules and libraries
             for systems missing tk/tcl support. (Set noGUI to True in the code)
Version 1.3: Added new column to hold log entries relating to each record. For example, a note stating that
             some characters in the filename were converted to hex as they could not be printed.
Version 1.4: Credit: Spencer Lynch. I was misusing the flags field in the MFT header. The first bit is
             Active/Inactive. The second bit is File/Folder.
Version 1.5: Fixed date/time reporting. I wasn't reporting useconds at all.
             Added anomaly detection. Adds two columns:
                    std-fn-shift:  If Y, entry's FN create time is after the STD create time
                    usec-zero: If Y, entry's STD create time's usec value is zero
Version 1.6: Various bug fixes
Version 1.7: Bodyfile support, with thanks to Dave Hull
Version 1.8: Added support for full path extraction, written by Kristinn Gudjonsson
Version 1.9: Added support for csv timeline output
Version 1.10: Just for Tom
Version 1.11: Fixed TSK bodyfile output
Version 1.12: Fix orphan file detection issue that caused recursion error (4/18/2013)
Version 1.13: Changed from walking all sequence numbers to pulling sequence number from MFT. Previous approach did not handle
              gaps well
Version 1.14: Made -o output optional if -b is specified. (Either/or)
Version 1.15: Added file size (real, not allocated) to bodyfile.
              Added bodyfile option to include fullpath + filename rather than just filename
              Added bodyfile option to use STD_INFO timestamps rather than FN timestamps


Version 2 history is in CHANGES.txt






Inspiration
===========
My original inspiration was a combination of MFT Ripper (thus the current output format) and the
SANS 508.1 study guide. I couldn't bear to read about NTFS structures again,
particularly since the information didn't "stick". I also wanted to learn Python
so I figured that using it to tear apart the MFT file was a reasonably sized
project.

Many of the variable names are taken directly from Brian Carrier's The Sleuth Kit. His code, plus his
book "File System Forensic Analysis", was very helpful in my efforts to write this code.

The output format is almost identical to Mark Menz's MFT Ripper. His tool really inspired me to learn
more about the structure of the MFT and to learn what additional information I could glean from
the data.

I also am getting much more interested in timeline analysis and figured that really understanding the
the MFT and having a tool that could parse it might serve as a good foundation
for further research in that area.


Future work
===========

1) Figure out how to write the CSV file in a manner that forces Excel to interpret the date/time
fields as text. If you add the .csv extension Excel will open the file without invoking the import
wizard and the date fields are treated as "General" and the date is chopped leaving just the time.
2) Add version switch
3) Add "mftr" switch - produce MFT Ripper compatible output
4) Add "extract" switch - extract or work on live MFT file
5) Finish parsing all possible attributes
6) Look into doing more timeline analysis with the information
7) Improve the documentation so I can use the structures as a reference and reuse the code more effectively
8) Clean up the code and, in particular, follow standard naming conventions
9) There are two MFT entry flags that appear that I can't determine the significance of. These appear in
    the output as Unknown1 and Unknown2
10) Parse filename based on 'nspace' value in FN structure
11) Test it and ensure that it works on all major Windows OS versions
12) Output HTML as well as CSV
13) If you specify a bad input filename and a good output filename, you get an
error about the output filename.


Useful Documentation
====================

1) http://dubeyko.com/development/FileSystems/NTFS/ntfsdoc.pdf

