import asyncio
import sys
from src.analyzeMFT.cli import main

# Adds the current directory to the path to ensure our file calls are consistent.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

if __name__ == "__main__":
    if sys.platform == "win32":
        # This sets the event loop policy to use the ProactorEventLoop on Windows
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())