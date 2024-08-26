# This format: MD5|name|inode|mode_as_string|UID|GID|size|atime|mtime|ctime|crtime

class BodyfileWriter:
    def __init__(self, output_file):
        self.output_file = output_file

    def _format_mode_as_string(self, mode):
        # Convert file mode to a string representation like 'rwxr-xr-x'
        is_dir = 'd' if os.path.isdir(mode) else '-'
        perm = ''
        for who in ('USR', 'GRP', 'OTH'):
            for what in ('R', 'W', 'X'):
                perm += (who + what) in os.popen(f'stat -c %A {mode}').read()[-4:] and what.lower() or '-'
        return is_dir + perm

    def _format_record(self, record):
        md5 = record.get('md5', '')
        name = record.get('filename', '')
        inode = record.get('inode', '0')
        mode = self._format_mode_as_string(record.get('mode', 0))
        uid = str(record.get('uid', '0'))
        gid = str(record.get('gid', '0'))
        size = str(record.get('size', '0'))
        atime = str(record.get('atime', '0'))
        mtime = str(record.get('mtime', '0'))
        ctime = str(record.get('ctime', '0'))
        crtime = str(record.get('crtime', '0'))

        return f"{md5}|{name}|{inode}|{mode}|{uid}|{gid}|{size}|{atime}|{mtime}|{ctime}|{crtime}"

    def write_records(self, records):
        with open(self.output_file, 'w') as bf:
            for record in records:
                formatted_record = self._format_record(record)
                bf.write(formatted_record + '\n')