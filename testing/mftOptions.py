#!/usr/bin/env python3
# Author: Benjamin Cance bjc@tdx.li
# Name: mftOptions.py
#
# Copyright (c) 2024 Benjamin Cance. All rights reserved.
# This software is distributed under the MIT License
#
# Date: July 2024
#
# File creation note:
#   Brought this over from mftSession.py
# 
# Changes from the original:
#
#  31-July-2024:
#     Added -t or --threading for future multithreading capabilities

from optparse import OptionParser

def parse_options():
    parser = OptionParser(usage="usage: %prog [options]")
    
    parser.add_option("-v", "--version", action="store_true", dest="version",
                      help="report version and exit")

    parser.add_option("-f", "--file", dest="filename",
                      help="read MFT from FILE", metavar="FILE")

    parser.add_option("-j", "--json", dest="json",
                      help="File paths should use the Windows path separator instead of Linux")

    parser.add_option("-o", "--output", dest="output",
                      help="write results to FILE", metavar="FILE")

    parser.add_option("-a", "--anomaly", action="store_true", dest="anomaly",
                      help="turn on anomaly detection")

    parser.add_option("-e", "--excel", action="store_true", dest="excel",
                      help="print date/time in Excel friendly format")

    parser.add_option("-b", "--bodyfile", dest="bodyfile",
                      help="write MAC information to bodyfile", metavar="FILE")

    parser.add_option("--bodystd", action="store_true", dest="bodystd",
                      help="Use STD_INFO timestamps for body file rather than FN timestamps")

    parser.add_option("--bodyfull", action="store_true", dest="bodyfull",
                      help="Use full path name + filename rather than just filename")

    parser.add_option("-c", "--csvtimefile", dest="csvtimefile",
                      help="write CSV format timeline file", metavar="FILE")

    parser.add_option("-l", "--localtz", action="store_true", dest="localtz",
                      help="report times using local timezone")

    parser.add_option("-d", "--debug", action="store_true", dest="debug",
                      help="turn on debugging output")

    parser.add_option("-s", "--saveinmemory", action="store_true", dest="inmemory",
                      help="Save a copy of the decoded MFT in memory. Do not use for very large MFTs")

    parser.add_option("-p", "--progress", action="store_true", dest="progress",
                      help="Show systematic progress reports.")

    parser.add_option("-w", "--windows-path", action="store_true", dest="winpath",
                      help="File paths should use the Windows path separator instead of Linux")

    parser.add_option("-t", "--threads", dest="threads", type="int", default=1,
                      help="Number of threads to use for processing (default is 1)")

    options, args = parser.parse_args()
    
    return options
