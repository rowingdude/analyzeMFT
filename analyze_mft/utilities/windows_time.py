from datetime import datetime, timezone, timedelta

class WindowsTime:
    WINDOWS_TICK = 10000000
    SECONDS_TO_UNIX_EPOCH = 11644473600

    def __init__(self, timestamp, localtz):
        self.timestamp = timestamp
        self.localtz = localtz
        self.dt = None
        self.dtstr = "Not defined"
        self.unixtime = 0
        self._parse_time()

    def _parse_time(self):
        if self.timestamp == 0:
            self.dtstr = "Never"
            return

        try:
            self.unixtime = self._calculate_unixtime()
            self.dt = self._create_datetime()
            self.dtstr = self.dt.isoformat()
        except (ValueError, OSError) as e:
            self.dtstr = f"Invalid timestamp: {e}"
            self.unixtime = 0

    def _calculate_unixtime(self):
        return (self.timestamp / self.WINDOWS_TICK) - self.SECONDS_TO_UNIX_EPOCH

    def _create_datetime(self):
        if self.unixtime < 0:
            # Handle dates before Unix epoch
            unix_epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
            return unix_epoch + timedelta(seconds=self.unixtime)
        else:
            if self.localtz:
                return datetime.fromtimestamp(self.unixtime).astimezone()
            else:
                return datetime.fromtimestamp(self.unixtime, tz=timezone.utc)

    def __str__(self):
        return self.dtstr

    def __repr__(self):
        return f"WindowsTime(timestamp={self.timestamp}, localtz={self.localtz}, dtstr='{self.dtstr}')"