from datetime import date, datetime
from optparse import OptionParser
import os

# DevelNote: need to pass in localtz now

class WindowsTime:
    "Convert the Windows time in 100 nanosecond intervals since Jan 1, 1601 to time in seconds since Jan 1, 1970"
    
    def __init__(self, low, high, localtz):
        self.low = long(low)
        self.high = long(high)
        
        if (low == 0) and (high == 0):
            self.dt = 0
            self.dtstr = "Not defined"
            self.unixtime = 0
            return
        
        # Windows NT time is specified as the number of 100 nanosecond intervals since January 1, 1601.
        # UNIX time is specified as the number of seconds since January 1, 1970. 
        # There are 134,774 days (or 11,644,473,600 seconds) between these dates.
        self.unixtime = self.GetUnixTime()
              
        try:
          if (localtz == True):
               self.dt = datetime.fromtimestamp(self.unixtime)
          else:
               self.dt = datetime.utcfromtimestamp(self.unixtime)

          # Pass isoformat a delimiter if you don't like the default "T".
          self.dtstr = self.dt.isoformat(' ')
          
        except:
          self.dt = 0
          self.dtstr = "Invalid timestamp"
          self.unixtime = 0
          
        
    def GetUnixTime(self):
        t=float(self.high)*2**32 + self.low

     # The '//' does a floor on the float value, where *1e-7 does not, resulting in an off by one second error
     # However, doing the floor loses the usecs....
        return (t*1e-7 - 11644473600)
     #return((t//10000000)-11644473600)



def mft_options():

    parser = OptionParser()
    parser.set_defaults(debug=False,UseLocalTimezone=False,UseGUI=False)
    
    parser.add_option("-v", "--version", action="store_true", dest="version",
                      help="report version and exit")
    
    parser.add_option("-f", "--file", dest="filename",
                      help="read MFT from FILE", metavar="FILE")
    
    parser.add_option("-o", "--output", dest="output",
                      help="write results to FILE", metavar="FILE")
    
    parser.add_option("-a", "--anomaly",
                      action="store_true", dest="anomaly",
                      help="turn on anomaly detection")
    
    parser.add_option("-b", "--bodyfile", dest="bodyfile",
                      help="write MAC information to bodyfile", metavar="FILE")
    
    parser.add_option("--bodystd", action="store_true", dest="bodystd",
                      help="Use STD_INFO timestamps for body file rather than FN timestamps")
    
    parser.add_option("--bodyfull", action="store_true", dest="bodyfull",
                      help="Use full path name + filename rather than just filename")
    
    parser.add_option("-c", "--csvtimefile", dest="csvtimefile",
                      help="write CSV format timeline file", metavar="FILE")
    
    parser.add_option("-l", "--localtz",
                      action="store_true", dest="localtz",
                      help="report times using local timezone")

    parser.add_option("-d", "--debug",
                      action="store_true", dest="debug",
                      help="turn on debugging output")
    
    (options, args) = parser.parse_args()
    
    return options
