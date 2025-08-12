from datetime import datetime, timezone
from typing import Optional

class WindowsTime:
    
    WINDOWS_EPOCH_DIFF: float = 11644473600.0  # Seconds between Windows and Unix epochs
    TICKS_PER_SECOND: float = 10000000.0       # 100-nanosecond intervals per second
    
    def __init__(self, low: int, high: int) -> None:
        self.low = int(low)
        self.high = int(high)
        
        if (self.low == 0) and (self.high == 0):
            self.dt: Optional[datetime] = None
            self.dtstr: str = "Not defined"
            self.unixtime: float = 0.0
            return
        
        self.unixtime = self.get_unix_time()
        
        try:
            if self.unixtime >= 0:
                self.dt = datetime.fromtimestamp(self.unixtime, tz=timezone.utc)
                self.dtstr = self.dt.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
            else:
                self.dt = None
                self.dtstr = "Invalid timestamp"
                self.unixtime = 0.0
        except (OSError, OverflowError, ValueError):
            self.dt = None
            self.dtstr = "Invalid timestamp"
            self.unixtime = 0.0

    def get_unix_time(self) -> float:
        timestamp = (self.high << 32) | self.low
        return (timestamp / self.TICKS_PER_SECOND) - self.WINDOWS_EPOCH_DIFF
    
    def __str__(self) -> str:
        return self.dtstr
    
    def __repr__(self) -> str:
        return f"WindowsTime(low={self.low}, high={self.high}, unixtime={self.unixtime})"
    
    def is_valid(self) -> bool:
        return self.dt is not None and self.unixtime != 0.0