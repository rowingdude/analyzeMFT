#!/usr/bin/env python

# Version 2.1.1.1
#
# Author: Benjamin Cance (bjc@tdx.li)
# Copyright Benjamin Cance 2024
#
# 2-Aug-24 
# - Updating to current PEP

from argparse import ArgumentParser
from typing import Dict, Any
from . import mftutils
from .mft_formatter import mft_to_csv, mft_to_body, mft_to_l2t
from .mftutils import decodeMFTmagic, decodeMFTisactive, decodeMFTrecordtype, decodeVolumeInfo, decodeObjectID, ObjectID

def set_default_options() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("--debug", action="store_true", default=False)
    parser.add_argument("--localtz", default=None)
    parser.add_argument("--bodystd", action="store_true", default=False)
    parser.add_argument("--bodyfull", action="store_true", default=False)
    return parser

