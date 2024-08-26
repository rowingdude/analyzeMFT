import argparse
import os
from functools import wraps
from analyze_mft.constants.constants import VERSION

def log_call(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"Finished {func.__name__}")
        return result
    return wrapper

class OptionsParser:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="Analyze MFT files")
        self._set_options()

    @log_call
    def _set_options(self):
        self._add_main_options()
        self._add_output_options()
        self._add_body_file_options()
        self._add_misc_options()
        self._add_performance_options()

    def _add_main_options(self):
        self.parser.add_argument("-f", "--file", dest="filename", required=True,
                                 help="Read MFT from FILE", metavar="FILE")

    def _add_output_options(self):
        group = self.parser.add_argument_group('Output Options')
        group.add_argument("-o", "--output", dest="output",
                           help="Write results to CSV FILE", metavar="FILE")
        group.add_argument("-b", "--bodyfile", dest="bodyfile",
                           help="Write MAC information to bodyfile", metavar="FILE")
        group.add_argument("-c", "--csvtimefile", dest="csvtimefile",
                           help="Write CSV format timeline file", metavar="FILE")
        group.add_argument("-j", "--json", dest="jsonfile",
                           help="Write results to JSON FILE", metavar="FILE")

    def _add_body_file_options(self):
        group = self.parser.add_argument_group('Body File Options')
        group.add_argument("--bodystd", action="store_true", dest="bodystd",
                           help="Use STD_INFO timestamps for body file rather than FN timestamps")
        group.add_argument("--bodyfull", action="store_true", dest="bodyfull",
                           help="Use full path name + filename rather than just filename")

    def _add_misc_options(self):
        group = self.parser.add_argument_group('Miscellaneous Options')
        group.add_argument("-a", "--anomaly", action="store_true", dest="anomaly",
                           help="Turn on anomaly detection")
        group.add_argument("-l", "--localtz", action="store_true", dest="localtz",
                           help="Report times using local timezone",default=True)
        group.add_argument("-d", "--debug", action="store_true", dest="debug",
                           help="Turn on debugging output")
        group.add_argument("-v", "--version", action="store_true", dest="version",
                           help="Report version and exit")
        group.add_argument("-V", "--verbose", action="store_true", dest="verbose",
                           help="Enable verbose output")
        group.add_argument("--log", dest="log_file",
                           help="Write debugging information to LOG_FILE", metavar="LOG_FILE")

    def _add_performance_options(self):
        group = self.parser.add_argument_group('Performance Options')
        group.add_argument("--threads", type=int, dest="thread_count", default=1,
                           help="Number of threads to use for parsing (default: 1)")

    @log_call
    def parse_options(self):
        options = self.parser.parse_args()
        self._validate_options(options)
        return options

    @log_call
    def _validate_options(self, options):
        self._check_version(options)
        self._check_file_exists(options)
        self._check_output_options(options)
        self._check_body_file_options(options)
        self._check_thread_count(options)
        return options

    def _check_version(self, options):
        if options.version:
            print(f"Version is: {VERSION}")
            exit(0)

    def _check_file_exists(self, options):
        if not os.path.exists(options.filename):
            self.parser.error(f"The specified file does not exist: {options.filename}")

    def _check_output_options(self, options):
        output_options = [options.output, options.bodyfile, options.csvtimefile, options.jsonfile]
        if not any(output_options):
            self.parser.error("At least one output option (-o, -b, -j, or -c) is required.")

    def _check_body_file_options(self, options):
        if (options.bodystd or options.bodyfull) and not options.bodyfile:
            self.parser.error("--bodystd and --bodyfull options require -b/--bodyfile option.")

    def _check_thread_count(self, options):
        if options.thread_count < 1:
            self.parser.error("Thread count must be at least 1")