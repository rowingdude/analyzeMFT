#!/usr/bin/env python3

import os
import sys
import asyncio

def setup_path():
    src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

def main():
    setup_path()
    from analyzeMFT.cli import main as cli_main
    
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(cli_main())

if __name__ == "__main__":
    main()