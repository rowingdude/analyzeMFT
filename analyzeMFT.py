#!/usr/bin/env python3

import os
import sys
import asyncio

def setup_path():
    # Try multiple paths to find src/analyzeMFT
    script_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(script_dir, 'src'),  # src/ in same directory as script
        os.path.join(script_dir, '..', 'src'),  # src/ in parent directory
        script_dir,  # current directory
    ]
    
    for path in possible_paths:
        src_path = os.path.abspath(path)
        analyzeMFT_path = os.path.join(src_path, 'analyzeMFT')
        if os.path.exists(analyzeMFT_path) and os.path.isdir(analyzeMFT_path):
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
            return
    
    # Fallback: add both current directory and src to path
    current_dir = os.getcwd()
    src_path = os.path.join(current_dir, 'src')
    for path in [src_path, current_dir]:
        if path not in sys.path:
            sys.path.insert(0, path)

def main():
    setup_path()
    # Debug information for GitHub Actions
    import sys
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"sys.path (first 5): {sys.path[:5]}")
    print(f"Contents of current directory: {os.listdir('.')}")
    if os.path.exists('src'):
        print(f"Contents of src directory: {os.listdir('src')}")
        if os.path.exists('src/analyzeMFT'):
            print(f"Contents of src/analyzeMFT directory: {os.listdir('src/analyzeMFT')}")
    
    try:
        from analyzeMFT.cli import main as cli_main
    except ImportError as e:
        print(f"Import error: {e}")
        # Try alternative import
        try:
            from src.analyzeMFT.cli import main as cli_main
            print("Successfully imported using src.analyzeMFT.cli")
        except ImportError as e2:
            print(f"Alternative import also failed: {e2}")
            raise
    
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(cli_main())

if __name__ == "__main__":
    main()