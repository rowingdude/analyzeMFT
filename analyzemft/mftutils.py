#!/usr/bin/env python

# Version 2.1
#
# Author: Benjamin Cance (bjc@tdx.li)
# Copyright Benjamin Cance 2024
#
# 2-Aug-24 
# - Updating to current PEP
# - Correctly calculate the Unix timestamp from Windows filetime

from datetime import datetime, timezone
from typing import Union

class WindowsTime:
    def __init__(self, low: int, high: int, localtz: bool):
        self.low = int(low)
        self.high = int(high)
        self.dt: Union[datetime, int] = 0
        self.dtstr: str = ""
        self.unixtime: float = 0.0

        if (low == 0) and (high == 0):
            self.dtstr = "Not defined"
            return

        self.unixtime = self.get_unix_time()

        try:
            if localtz:
                self.dt = datetime.fromtimestamp(self.unixtime)
            else:
                # Use timezone-aware object for UTC
                self.dt = datetime.fromtimestamp(self.unixtime, tz=timezone.utc)
            
            self.dtstr = self.dt.isoformat(' ')
        except:
            self.dtstr = "Invalid timestamp"
            self.unixtime = 0.0

    def get_unix_time(self) -> float:
        wintime = (self.high << 32) | self.low
        unix_time = wintime / 10000000 - 11644473600
        return unix_time

    def __str__(self):
        return self.dtstr
