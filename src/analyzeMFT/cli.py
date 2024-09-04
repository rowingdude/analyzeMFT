import asyncio
from optparse import OptionParser, OptionGroup
import sys
from .mft_analyzer import MftAnalyzer
from .constants import VERSION

async def main():
    parser = OptionParser(usage="usage: %prog -f <mft_file> -o <output_file> [options]",
                          version=f"%prog {VERSION}")
    parser.add_option("-f", "--file", dest="filename",
                      help="MFT file to analyze", metavar="FILE")
    parser.add_option("-o", "--output", dest="output_file",
                      help="Output file", metavar="FILE")
    
    export_group = OptionGroup(parser, "Export Options")
    export_group.add_option("--csv", action="store_const", const="csv", dest="export_format",
                            help="Export as CSV (default)")
    export_group.add_option("--json", action="store_const", const="json", dest="export_format",
                            help="Export as JSON")
    export_group.add_option("--xml", action="store_const", const="xml", dest="export_format",
                            help="Export as XML")
    export_group.add_option("--excel", action="store_const", const="excel", dest="export_format",
                            help="Export as Excel")
    export_group.add_option("--body", action="store_const", const="body", dest="export_format",
                            help="Export as body file (for mactime)")
    export_group.add_option("--timeline", action="store_const", const="timeline", dest="export_format",
                            help="Export as TSK timeline")
    export_group.add_option("--l2t", action="store_const", const="l2t", dest="export_format",
                            help="Export as log2timeline CSV")
    parser.add_option_group(export_group)

    verbosity_group = OptionGroup(parser, "Verbosity Options")
    verbosity_group.add_option("-v", "--verbose", action="count", dest="verbosity",
                               help="Increase output verbosity (can be used multiple times)", default=0)
    verbosity_group.add_option("-d", "--debug", action="store_true", dest="debug",
                               help="Enable debug output", default=False)
    verbosity_group.add_option("-dd", "--very-debug", action="store_true", dest="very_debug",
                               help="Enable very verbose debug output", default=False)
    parser.add_option_group(verbosity_group)

    parser.add_option("-H", "--hash", action="store_true", dest="compute_hashes",
                      help="Compute hashes (MD5, SHA256, SHA512, CRC32)", default=False)

    (options, args) = parser.parse_args()

    if not options.filename or not options.output_file:
        parser.print_help()
        sys.exit(1)

    if not options.export_format:
        options.export_format = "csv"  # Default to CSV if no format specified

    analyzer = MftAnalyzer(options.filename, options.output_file, options.debug, options.very_debug, 
                           options.verbosity, options.compute_hashes, options.export_format)
    await analyzer.analyze()
    print(f"Analysis complete. Results written to {options.output_file}")

if __name__ == "__main__":
    asyncio.run(main())