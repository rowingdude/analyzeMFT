# Version 2.1.1
#
# Author: Benjamin Cance (bjc@tdx.li)
#
# 2-Aug-24 
# - Updating to current PEP

import sys
import logging
from analyzemft import mftsession

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        session = mftsession.MftSession()
        session.mft_options()
        session.run()
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()