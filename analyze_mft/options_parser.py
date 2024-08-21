from .common_imports import *
from optparse import OptionParser
from .constants import VERSION

class OptionsParser:
    def __init__(self):
        self.parser = OptionParser()
        self._set_options()

    def _set_options(self):
        self.parser.add_option("-f", "--file", dest="filename",
                               help="read MFT from FILE", metavar="FILE")
        self.parser.add_option("-o", "--output", dest="output",
                               help="write results to FILE", metavar="FILE")
        self.parser.add_option("-a", "--anomaly", action="store_true", dest="anomaly",
                               help="turn on anomaly detection")
        self.parser.add_option("-b", "--bodyfile", dest="bodyfile",
                               help="write MAC information to bodyfile", metavar="FILE")
        self.parser.add_option("--bodystd", action="store_true", dest="bodystd",
                               help="Use STD_INFO timestamps for body file rather than FN timestamps")
        self.parser.add_option("--bodyfull", action="store_true", dest="bodyfull",
                               help="Use full path name + filename rather than just filename")
        self.parser.add_option("-c", "--csvtimefile", dest="csvtimefile",
                               help="write CSV format timeline file", metavar="FILE")
        self.parser.add_option("-l", "--localtz", action="store_true", dest="localtz",
                               help="report times using local timezone")
        self.parser.add_option("-d", "--debug", action="store_true", dest="debug",
                               help="turn on debugging output")
        self.parser.add_option("-v", "--version", action="store_true", dest="version",
                               help="report version and exit")

    def parse_options(self):
        options, _ = self.parser.parse_args()
        self._validate_options(options)
        return options

    def _validate_options(self, options):
        if options.version:
            print(f"Version is: {VERSION}")
            sys.exit()

        if options.filename is None:
            print("-f <filename> required.")
            sys.exit()

        if options.output is None and options.bodyfile is None and options.csvtimefile is None:
            print("-o <filename> or -b <filename> or -c <filename> required.")
            sys.exit()