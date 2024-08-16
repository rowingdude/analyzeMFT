from .common_imports import *
from datetime import datetime, timezone

class WindowsTime:
    def __init__(self, low, high, localtz):

        if not isinstance(low, int) or not isinstance(high, int):
            raise ValueError("Low and high values must be integers")
        
        if not isinstance(localtz, bool):
            raise ValueError("localtz must be a boolean value")

        self.low = int(low)
        self.high = int(high)
        self.localtz = localtz
        self.dt = None
        self.dtstr = "Not defined"
        self.unixtime = 0
        self._parse_time()

    def _parse_time(self):

        if (self.low == 0) and (self.high == 0):
            self.dtstr = "Never"
            return
        
        try:
            self.unixtime = self.get_unix_time()
            
            if self.unixtime < 0:
                raise ValueError("Negative Unix time calculated")
            
            if self.localtz:
                self.dt = datetime.fromtimestamp(self.unixtime).astimezone()

            else:
                self.dt = datetime.fromtimestamp(self.unixtime, tz=timezone.utc)
            
            self.dtstr = self.dt.isoformat()
          
        except (ValueError, OverflowError) as e:

            self.dtstr = f"Invalid timestamp: {e}"
            self.unixtime = 0

    def get_unix_time(self):

        t = float(self.high) * 2**32 + self.low
        
        return (t * 1e-7 - 11644473600)
