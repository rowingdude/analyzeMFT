from .common_imports import *
from datetime import datetime, timezone

class WindowsTime:
    def __init__(self, low, high, localtz):
        self.low = int(low)
        self.high = int(high)
        self.localtz = localtz
        self.dt = None
        self.dtstr = "Not defined"
        self.unixtime = 0
        self._parse_time()

    def _parse_time(self):
        if (self.low == 0) and (self.high == 0):
            return
        
        self.unixtime = self.get_unix_time()
              
        try:
            if self.localtz:
                self.dt = datetime.fromtimestamp(self.unixtime).astimezone()
            else:
                self.dt = datetime.fromtimestamp(self.unixtime, tz=timezone.utc)
            
            self.dtstr = self.dt.isoformat()
          
        except Exception as e:
            self.dtstr = f"Invalid timestamp: {e}"
            self.unixtime = 0

    def get_unix_time(self):
        t = float(self.high) * 2**32 + self.low
        return (t * 1e-7 - 11644473600)
