#!/usr/bin/env python3
# Author: Benjamin Cance [ maintainer <at> analyzemft [dot] com ]
# Name: mftsession.py
#
# Copyright (c) 2024 Benjamin Cance. All rights reserved.
# This software is distributed under the MIT License
#
# Date: May 2024
#


def parse_little_endian_signed_positive(buf):
    ret = 0
    for i, b in enumerate(buf):
        ret += b * (1 << (i * 8))
    return ret


def parse_little_endian_signed_negative(buf):
    ret = 0
    for i, b in enumerate(buf):
        ret += (b ^ 0xFF) * (1 << (i * 8))
    ret += 1

    ret *= -1
    return ret


def parse_little_endian_signed(buf):
  
  if not buf:
      raise ValueError("Empty buffer")

  value = 0
  size = len(buf)
  for i in range(size):
      value |= buf[i] << (i * 8)

  if value & (1 << ((size * 8) - 1)):
      value = - (value + (1 << size * 8))

  return value