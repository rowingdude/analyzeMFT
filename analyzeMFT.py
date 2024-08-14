# Version 2.1.1
#
# Author: Benjamin Cance (bjc@tdx.li)
#
# 2-Aug-24 
# - Updating to current PEP


import sys
import logging
from analyzemft.config import Config
from analyzemft.mft_session import MftSession
from analyzemft.error_handler import setup_logging, MFTAnalysisError, ConfigurationError

def main():
    try:
        config = Config()
        config.parse_args()
        conf = config.get_config()

        setup_logging(conf['log_level'])

        session = MftSession(conf)
        session.run()

    except ConfigurationError as e:
        logging.error(f"Configuration error: {e}")
        sys.exit(1)
    except MFTAnalysisError as e:
        logging.error(f"MFT analysis error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logging.info("Analysis interrupted by user")
        sys.exit(0)
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
