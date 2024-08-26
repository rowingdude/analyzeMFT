from datetime import datetime, timezone, timedelta

class WindowsTime:
    WINDOWS_TICK = 10000000
    SECONDS_TO_UNIX_EPOCH = 11644473600

    def __init__(self, timestamp: int, localtz: bool):
        self.timestamp = timestamp
        self.localtz = localtz
        self.dt = None
        self.dtstr = self._format_timestamp()

    def _format_timestamp(self) -> str:
        if self.timestamp == 0:
            return "Never"

        try:
            unixtime = self._calculate_unixtime()
            self.dt = self._create_datetime(unixtime)
            return self.dt.isoformat()
        except (ValueError, OSError) as e:
            self.dt = None
            return f"Invalid timestamp: {e}"

    def _calculate_unixtime(self) -> float:
        return (self.timestamp / self.WINDOWS_TICK) - self.SECONDS_TO_UNIX_EPOCH

    def _create_datetime(self, unixtime: float) -> datetime:
        if unixtime < 0:
            unix_epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
            return unix_epoch + timedelta(seconds=unixtime)
        return datetime.fromtimestamp(unixtime, tz=timezone.utc).astimezone() if self.localtz else datetime.fromtimestamp(unixtime, tz=timezone.utc)

    def __str__(self) -> str:
        return self.dtstr

    def __repr__(self) -> str:
        return f"WindowsTime(timestamp={self.timestamp}, localtz={self.localtz}, dtstr='{self.dtstr}')"
