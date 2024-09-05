import os
import sys
import asyncio
from src.analyzeMFT.cli import main

# Adds the current directory to the path to ensure our file calls are consistent.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())