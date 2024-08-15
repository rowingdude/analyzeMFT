from .common_imports import *
from .windows_time import WindowsTime

class AttributeParser:
    def __init__(self, raw_data, options):
        self.raw_data = raw_data
        self.options = options

    def parse(self):
        return self.decode_attribute_header()

    def decode_attribute_header(self):
        d = {}
        d['type'] = struct.unpack("<I", self.raw_data[:4])[0]
        if d['type'] == 0xffffffff:
            return d
        d['len'] = struct.unpack("<I", self.raw_data[4:8])[0]
        d['res'] = struct.unpack("B", self.raw_data[8:9])[0]
        d['name_off'] = struct.unpack("<H", self.raw_data[10:12])[0]
        d['flags'] = struct.unpack("<H", self.raw_data[12:14])[0]
        d['id'] = struct.unpack("<H", self.raw_data[14:16])[0]
        if d['res'] == 0:
            d['ssize'] = struct.unpack("<L", self.raw_data[16:20])[0]
            d['soff'] = struct.unpack("<H", self.raw_data[20:22])[0]
            d['idxflag'] = struct.unpack("<H", self.raw_data[22:24])[0]
        else:
            d['start_vcn'] = struct.unpack("<d", self.raw_data[16:24])[0]
            d['last_vcn'] = struct.unpack("<d", self.raw_data[24:32])[0]
            d['run_off'] = struct.unpack("<H", self.raw_data[32:34])[0]
            d['compusize'] = struct.unpack("<H", self.raw_data[34:36])[0]
            d['f1'] = struct.unpack("<I", self.raw_data[36:40])[0]
            d['alen'] = struct.unpack("<d", self.raw_data[40:48])[0]
            d['ssize'] = struct.unpack("<d", self.raw_data[48:56])[0]
            d['initsize'] = struct.unpack("<d", self.raw_data[56:64])[0]
        return d

    def parse_standard_information(self):
        d = {}
        s = self.raw_data[self.decode_attribute_header()['soff']:]
        d['crtime'] = WindowsTime(struct.unpack("<L", s[:4])[0], struct.unpack("<L", s[4:8])[0], self.options.localtz)
        d['mtime'] = WindowsTime(struct.unpack("<L", s[8:12])[0], struct.unpack("<L", s[12:16])[0], self.options.localtz)
        d['ctime'] = WindowsTime(struct.unpack("<L", s[16:20])[0], struct.unpack("<L", s[20:24])[0], self.options.localtz)
        d['atime'] = WindowsTime(struct.unpack("<L", s[24:28])[0], struct.unpack("<L", s[28:32])[0], self.options.localtz)
        d['dos'] = struct.unpack("<I", s[32:36])[0]
        d['maxver'] = struct.unpack("<I", s[36:40])[0]
        d['ver'] = struct.unpack("<I", s[40:44])[0]
        d['class_id'] = struct.unpack("<I", s[44:48])[0]
        d['own_id'] = struct.unpack("<I", s[48:52])[0]
        d['sec_id'] = struct.unpack("<I", s[52:56])[0]
        d['quota'] = struct.unpack("<d", s[56:64])[0]
        d['usn'] = struct.unpack("<d", s[64:72])[0]
        return d

    def parse_file_name(self, record):
        d = {}
        s = self.raw_data[self.decode_attribute_header()['soff']:]
        d['par_ref'] = struct.unpack("<Lxx", s[:6])[0]
        d['par_seq'] = struct.unpack("<H", s[6:8])[0]
        d['crtime'] = WindowsTime(struct.unpack("<L", s[8:12])[0], struct.unpack("<L", s[12:16])[0], self.options.localtz)
        d['mtime'] = WindowsTime(struct.unpack("<L", s[16:20])[0], struct.unpack("<L", s[20:24])[0], self.options.localtz)
        d['ctime'] = WindowsTime(struct.unpack("<L", s[24:28])[0], struct.unpack("<L", s[28:32])[0], self.options.localtz)
        d['atime'] = WindowsTime(struct.unpack("<L", s[32:36])[0], struct.unpack("<L", s[36:40])[0], self.options.localtz)
        d['alloc_fsize'] = struct.unpack("<q", s[40:48])[0]
        d['real_fsize'] = struct.unpack("<q", s[48:56])[0]
        d['flags'] = struct.unpack("<d", s[56:64])[0]
        d['nlen'] = struct.unpack("B", s[64:65])[0]  
        d['nspace'] = struct.unpack("B", s[65:66])[0]

        bytes_left = d['nlen']*2
        d['name'] = s[66:66+bytes_left].decode('utf-16-le')

        return d