import pytest
from src.analyzeMFT.windows_time import WindowsTime
from datetime import datetime, timezone

def test_windows_time_initialization():
    wt = WindowsTime(0, 0)
    assert wt.dt is None
    assert wt.dtstr == "Not defined"
    assert wt.unixtime == 0

def test_windows_time_conversion():    filetime = 132854688000000000
    low = filetime & 0xFFFFFFFF
    high = filetime >> 32
    wt = WindowsTime(low, high)
    assert wt.dt.year == 2022
    assert wt.dt.month == 1
    assert wt.dt.day == 1
    assert wt.unixtime == 1640995200.0

def test_invalid_time():    wt = WindowsTime(0xFFFFFFFF, 0xFFFFFFFF)
    assert wt.dt is None
    assert wt.dtstr == "Invalid timestamp"
    assert wt.unixtime == 0

def test_windows_time_far_past():    wt = WindowsTime(0, 0)
    assert wt.dt is None    assert wt.dtstr == "Not defined"

def test_windows_time_far_future():    filetime = 135379296000000000    low = filetime & 0xFFFFFFFF
    high = filetime >> 32
    wt = WindowsTime(low, high)
    assert wt.dt.year == 2030
    assert wt.dt.month == 1
    assert wt.dt.day == 1

def test_windows_time_dst_transition():    filetime = 131023080000000000    low = filetime & 0xFFFFFFFF
    high = filetime >> 32
    wt = WindowsTime(low, high)
    assert wt.dt.hour == 2
    assert wt.dt.minute == 0
    assert wt.dt.tzinfo == timezone.utc  # Ensure the time is in UTC