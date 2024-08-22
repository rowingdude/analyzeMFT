from .common_imports import *

class WindowsTime:
    def __init__(self, *args):
        if len(args) == 4:  # low, high, timestamp, localtz
            self.low, self.high, self.timestamp, self.localtz = args
        elif len(args) == 2:  # timestamp, localtz
            self.timestamp, self.localtz = args
            self.low = self.high = None
        else:
            raise ValueError("Invalid number of arguments")

        self._validate_inputs()
        self.dt = None
        self.dtstr = "Not defined"
        self.unixtime = 0
        self._parse_time()
        self.logger = logging.getLogger('analyzeMFT')

    def _validate_inputs(self):
        if self.low is not None and (not isinstance(self.low, int) or not isinstance(self.high, int)):
            raise ValueError("Low and high values must be integers")
        if not isinstance(self.timestamp, int):
            raise ValueError("Timestamp must be an integer")
        if not isinstance(self.localtz, bool):
            raise ValueError("localtz must be a boolean value")

    def _parse_time(self):
        if self.timestamp == 0:
            self.dtstr = "Never"
            self.logger.debug(f"Zero timestamp encountered")
            return

        try:
            self.unixtime = self._calculate_unixtime()
            if self.unixtime < 0:
                raise ValueError("Negative Unix time calculated")

            self.dt = self._create_datetime()
            self.dtstr = self.dt.isoformat()
            self.logger.debug(f"Parsed Windows time: {self.dtstr}")

        except (ValueError, OverflowError) as e:
            self.dtstr = f"Invalid timestamp: {e}"
            self.unixtime = 0
            self.logger.warning(f"Invalid timestamp encountered: {e}")

    def _calculate_unixtime(self):
        if self.low is not None and self.high is not None:
            return self.get_unix_time()
        else:
            return (self.timestamp / 10000000) - 11644473600

    def _create_datetime(self):
        if self.localtz:
            return datetime.fromtimestamp(self.unixtime).astimezone()
        else:
            return datetime.fromtimestamp(self.unixtime, tz=timezone.utc)

    def get_unix_time(self):
        if self.low is None or self.high is None:
            raise ValueError("Low and high values are not set")
        t = float(self.high) * 2**32 + self.low
        return (t * 1e-7 - 11644473600)

    def __str__(self):
        return self.dtstr

    def __repr__(self):
        return f"WindowsTime(timestamp={self.timestamp}, localtz={self.localtz}, dtstr='{self.dtstr}')"

    __all__ = ['WindowsTime']