import asyncio
from optparse import OptionParser
import sys
from .mft_analyzer import MftAnalyzer
from .constants import VERSION

async def main() -> None:
    parser = OptionParser(usage="usage: %prog -f <mft_file> -o <output.csv> [-d] [-H]",
                          version=f"%prog {VERSION}")
    parser.add_option("-f", "--file", dest="filename",
                      help="MFT file to analyze", metavar="FILE")
    parser.add_option("-o", "--output", dest="csvfile",
                      help="Output CSV file", metavar="FILE")
    parser.add_option("-d", "--debug", action="store_true", dest="debug",
                      help="Enable debug output", default=False)
    parser.add_option("-H", "--hash", action="store_true", dest="compute_hashes",
                      help="Compute hashes (MD5, SHA256, SHA512, CRC32)", default=False)

    (options, args) = parser.parse_args()

    if not options.filename or not options.csvfile:
        parser.print_help()
        sys.exit(1)

    analyzer = MftAnalyzer(options.filename, options.csvfile, options.debug, options.compute_hashes)
    await analyzer.analyze()
    print(f"Analysis complete. Results written to {options.csvfile}")

if __name__ == "__main__":
    asyncio.run(main())