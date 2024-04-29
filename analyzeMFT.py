#!/usr/bin/env python3

# Author: Benjamin Cance [ maintainer <at> analyzemft [dot] com ]
# Name: mftsession.py
#
# Copyright (c) 2024 Benjamin Cance. All rights reserved.
# This software is distributed under the MIT License
#
# Date: May 2024
#

try:
    from analyzemft import mftsession
except:
    from .analyzemft import mftsession

if __name__ == "__main__":
    session = mftsession.MftSession()
    session.mft_options()
    session.open_files()
    session.process_mft_file()
