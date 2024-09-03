import asyncio
import sys
from src.analyzeMFT.cli import main

if __name__ == "__main__":
    if sys.platform == "win32":
        # This sets the event loop policy to use the ProactorEventLoop on Windows
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())