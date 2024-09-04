from datetime import datetime, timezone

class WindowsTime:
    def __init__(self, low: int, high: int) -> None:
        self.low = int(low)
        self.high = int(high)
        
        if (low == 0) and (high == 0):
            self.dt = None
            self.dtstr = "Not defined"
            self.unixtime = 0
            return
        
        self.unixtime = self.get_unix_time()
        
        try:
            self.dt = datetime.fromtimestamp(self.unixtime, tz=timezone.utc)
            self.dtstr = self.dt.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        except:
            self.dt = None
            self.dtstr = "Invalid timestamp"
            self.unixtime = 0

    def get_unix_time(self) -> float:
        t = float(self.high) * 2**32 + self.low
        return (t / 10000000) - 11644473600 