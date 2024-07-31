#!/usr/bin/env python3
# Author: Benjamin Cance bjc@tdx.li
# Name: bitparse.py
#
# Copyright (c) 2024 Benjamin Cance. All rights reserved.
# This software is distributed under the MIT License
#
# Date: May 2024
#
# 31- July 2024
#
# Fixed error in parse_little_endian_signed:
#      If the sign bit is set, the function adjusts the value to represent a negative number using two's complement notation.

from typing import List

def parse_little_endian_signed_positive(buf: List[int]) -> int:
    ret = 0
    for i, b in enumerate(buf):
        ret += b * (1 << (i * 8))
    return ret

def parse_little_endian_signed_negative(buf: List[int], size: int) -> int:
    if not buf:
        raise ValueError("Empty buffer")

    if len(buf) != size:
        raise ValueError(f"Buffer size should be {size} bytes")

    sign_bit = 1 << ((size * 8) - 1)
    value = parse_little_endian_signed(buf, size)

    if value & sign_bit:
        value -= 1 << (size * 8) 

    return value

def parse_little_endian_signed(buf: List[int], size: int = 4) -> int:
    if not buf:
        raise ValueError("Empty buffer")

    value = 0
    for i in range(size):
        value |= buf[i] << (i * 8)

    if value & (1 << ((size * 8) - 1)):
        value = - (value + (1 << (size * 8)))

    return value