import pytest
from src.analyzeMFT.windows_time import WindowsTime
from datetime import datetime, timezone

def test_windows_time_initialization():
    wt = WindowsTime(0, 0)
    assert wt.dt is None
    assert wt.dtstr == "Not defined"
    assert wt.unixtime == 0

def test_windows_time_conversion():
    # 2022-01-01 00:00:00 UTC as Windows FILETIME
    # FILETIME: 132854688000000000 
    # Split into low and high 32-bit values
    filetime = 132854688000000000
    low = filetime & 0xFFFFFFFF
    high = filetime >> 32
    wt = WindowsTime(low, high)
    assert wt.dt.year == 2022
    assert wt.dt.month == 1
    assert wt.dt.day == 1
    assert wt.unixtime == 1640995200.0

def test_invalid_time():
    # Use very large values that will cause overflow
    wt = WindowsTime(0xFFFFFFFF, 0xFFFFFFFF)
    assert wt.dt is None
    assert wt.dtstr == "Invalid timestamp"
    assert wt.unixtime == 0

def test_windows_time_far_past():
    # Test a date in the year 1601 (Windows FILETIME epoch)
    # FILETIME 0 = January 1, 1601 00:00:00 UTC
    wt = WindowsTime(0, 0)
    assert wt.dt is None  # This is a special case that returns None
    assert wt.dtstr == "Not defined"

def test_windows_time_far_future():
    # Test a date in the future (year 2030)
    # FILETIME for 2030-01-01 00:00:00 UTC
    filetime = 135379296000000000  # 2030-01-01 00:00:00 UTC
    low = filetime & 0xFFFFFFFF
    high = filetime >> 32
    wt = WindowsTime(low, high)
    assert wt.dt.year == 2030
    assert wt.dt.month == 1
    assert wt.dt.day == 1

def test_windows_time_dst_transition():
    # Test a time during Daylight Saving Time transition
    # March 13, 2016, 2:00 AM UTC 
    filetime = 131023080000000000  # March 13, 2016, 2:00 AM UTC
    low = filetime & 0xFFFFFFFF
    high = filetime >> 32
    wt = WindowsTime(low, high)
    assert wt.dt.hour == 2
    assert wt.dt.minute == 0
    assert wt.dt.tzinfo == timezone.utc  # Ensure the time is in UTC