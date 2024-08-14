# Version 2.1.1
#
# Author: Benjamin Cance (bjc@tdx.li)
#
# 2-Aug-24 
# - Updating to current PEP

import logging
import sys
from analyzemft.mft_session import MftSession
from analyzemft.config import Config
from analyzemft.error_handler import setup_logging, MFTAnalysisError

def main():
    config = Config()
    config.parse_args()
    conf = config.get_config()

    setup_logging(conf['log_level'])

    try:
        session = MftSession(conf)
        session.run()
    except MFTAnalysisError as e:
        logging.error(f"MFT analysis failed: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
