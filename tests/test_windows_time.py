import pytest
from src.analyzeMFT.windows_time import WindowsTime
from datetime import datetime, timezone

def test_windows_time_initialization():
    wt = WindowsTime(0, 0)
    assert wt.dt is None
    assert wt.dtstr == "Not defined"
    assert wt.unixtime == 0

def test_windows_time_conversion():
    # 2022-01-01 00:00:00 UTC
    wt = WindowsTime(1845734400000000, 132854016000000000)
    assert wt.dt.year == 2022
    assert wt.dt.month == 1
    assert wt.dt.day == 1
    assert wt.unixtime == 1640995200.0

def test_invalid_time():
    wt = WindowsTime(-1, -1)
    assert wt.dt is None
    assert wt.dtstr == "Invalid timestamp"
    assert wt.unixtime == 0

def test_windows_time_far_past():
    # Test a date in the year 1601 (Windows FILETIME epoch)
    wt = WindowsTime(0, 1)
    assert wt.dt.year == 1601
    assert wt.dt.month == 1
    assert wt.dt.day == 1

def test_windows_time_far_future():
    # Test a date far in the future (year 9999)
    wt = WindowsTime(0, 2650467743999999999)
    assert wt.dt.year == 9999
    assert wt.dt.month == 12
    assert wt.dt.day == 31

def test_windows_time_dst_transition():
    # Test a time during Daylight Saving Time transition
    # This is a simplistic test and may need adjustment based on your specific needs
    wt = WindowsTime(0, 131242608000000000)  # March 13, 2016, 2:00 AM (just after DST starts in the US)
    assert wt.dt.hour == 2
    assert wt.dt.minute == 0
    assert wt.dt.tzinfo == timezone.utc  # Ensure the time is in UTC