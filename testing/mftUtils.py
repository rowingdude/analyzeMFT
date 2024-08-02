#!/usr/bin/env python3

# Author: Benjamin Cance [ bjc <at> tdx [dot] li ]
# Name: mftutils.py
#
# Copyright (c) 2024 Benjamin Cance. All rights reserved.
# This software is distributed under the MIT License
#
# Date: May 2024
#
# Changes:
# 
# 31-July-2024: 
#           
#       a. Added datetime/timezone support + UTC support 
#       b. Added typehints    
#       c. Updated 'quotechars' to use modern Python string conventions    
#       d. More descriptive error messages from WindowsTime errors
#       e. Updated ourput strings to 'f' strings for better aesthetics

from datetime import datetime, timezone
from typing import Union

# Converts Windows time ...
#  Input in 100 nanosecond intervals since Jan 1, 1601.
#  Output is Unix time which is seconds since Jan 1, 1970.
class WindowsTime:
  
    def __init__(self, low: Union[int, str], 
                      high: Union[int, str], 
                   localtz: bool            ):
        
        self.low  = int(low)
        self.high = int(high)

        if self.low == 0 and self.high == 0:
            self.dt       = None
            self.dtstr    = "Not defined"
            self.unixtime = 0
            return

        self.unixtime = self.get_unix_time()

        try:
            if localtz:
                self.dt = datetime.fromtimestamp(self.unixtime)
            else:
                self.dt = datetime.fromtimestamp(self.unixtime, tz=timezone.utc)

            self.dtstr  = self.dt.isoformat(' ')

        except (OSError, OverflowError, ValueError) as e:
            self.dt       = None
            self.dtstr    = f"Invalid timestamp: {e}"
            self.unixtime = 0

    # Converts Windows time to Unix time.
    def get_unix_time(self) -> float:
        t = float(self.high) * 2 ** 32 + self.low
        return t * 1e-7 - 11644473600

# Generate a hexdump of the given string: 
def hexdump(chars: str, sep: str, width: int) -> None:
    
    while chars:
        line  = chars[:width]
        chars = chars[width:]
        line  = line.ljust(width, '\000')
        print(f"{sep.join(f'{ord(c):02x}' for c in line)}{sep}{quotechars(line)}")


# Returns a string with non-alphanumeric characters replaced by a dot:
def quotechars(chars: str) -> str: 
    
    return ''.join(c if c.isalnum() else '.' for c in chars)
