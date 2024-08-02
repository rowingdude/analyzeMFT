# Version 2.1
#
# Author: Benjamin Cance (bjc@tdx.li)
#
# 2-Aug-24 
# - Updating to current PEP

import sys
from analyzemft import mftsession

if __name__ == "__main__":
    session = mftsession.MftSession()
    session.mft_options()
    session.open_files()
    session.process_mft_file()
    session.print_records()