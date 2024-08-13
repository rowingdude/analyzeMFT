# Version 2.1.1
#
# Author: Benjamin Cance (bjc@tdx.li)
#
# 2-Aug-24 
# - Updating to current PEP

import sys
import logging
from analyzemft import mft_session
from analyzemft.mft import set_default_options

def main():
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        # Get the command line options
        parser = set_default_options()
        options = parser.parse_args()
        
        # Create and initialize the MftSession
        session = mft_session.MftSession()
        session.options = options

        # Set up debug logging if requested
        if options.debug:
            logging.getLogger().setLevel(logging.DEBUG)

        # Run the MFT analysis
        session.open_files()
        session.process_mft_file()
        session.print_records()
        session.close_files()

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
