from .common_imports import *
from optparse import OptionParser, OptionGroup
from .constants import VERSION

class OptionsParser:
    def __init__(self):
        self.parser = OptionParser(usage="usage: %prog [options] filename")
        self._set_options()

    def _set_options(self):
        self.parser.add_option("-f", "--file", dest="filename",
                               help="Read MFT from FILE", metavar="FILE")
        
        # Output options
        output_group = OptionGroup(self.parser, "Output Options")
        output_group.add_option("-o", "--output", dest="output",
                                help="Write results to CSV FILE", metavar="FILE")
        output_group.add_option("-b", "--bodyfile", dest="bodyfile",
                                help="Write MAC information to bodyfile", metavar="FILE")
        output_group.add_option("-c", "--csvtimefile", dest="csvtimefile",
                                help="Write CSV format timeline file", metavar="FILE")
        self.parser.add_option_group(output_group)

        # Body file options
        body_group = OptionGroup(self.parser, "Body File Options")
        body_group.add_option("--bodystd", action="store_true", dest="bodystd",
                              help="Use STD_INFO timestamps for body file rather than FN timestamps")
        body_group.add_option("--bodyfull", action="store_true", dest="bodyfull",
                              help="Use full path name + filename rather than just filename")
        self.parser.add_option_group(body_group)

        # Other options
        self.parser.add_option("-a", "--anomaly", action="store_true", dest="anomaly",
                               help="Turn on anomaly detection")
        self.parser.add_option("-l", "--localtz", action="store_true", dest="localtz",
                               help="Report times using local timezone")
        self.parser.add_option("-d", "--debug", action="store_true", dest="debug",
                               help="Turn on debugging output")
        self.parser.add_option("-v", "--version", action="store_true", dest="version",
                               help="Report version and exit")

        # Performance options
        performance_group = OptionGroup(self.parser, "Performance Options")
        performance_group.add_option("--threads", type="int", dest="thread_count", default=1,
                                     help="Number of threads to use for parsing (default: 1)")
        self.parser.add_option_group(performance_group)

    def parse_options(self):
        options, args = self.parser.parse_args()
        self._validate_options(options, args)
        return options

    def _validate_options(self, options, args):
        if options.version:
            print(f"Version is: {VERSION}")
            sys.exit(0)

        if not args and not options.filename:
            self.parser.error("A filename is required.")

        if not options.filename:
            options.filename = args[0]

        output_options = [options.output, options.bodyfile, options.csvtimefile]
        if not any(output_options):
            self.parser.error("At least one output option (-o, -b, or -c) is required.")

        if options.bodystd or options.bodyfull:
            if not options.bodyfile:
                self.parser.error("--bodystd and --bodyfull options require -b/--bodyfile option.")

        if options.thread_count < 1:
            self.parser.error("Thread count must be at least 1")

        return options