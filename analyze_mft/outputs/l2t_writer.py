# Format: date,time,timezone,MACB,source,sourcetype,type,user,host,short,desc,version,filename,inode,notes,format

class L2TWriter:
    def __init__(self, output_file):
        self.output_file = output_file
        self.fields = [
            'date', 'time', 'timezone', 'MACB', 'source', 'sourcetype',
            'type', 'user', 'host', 'short', 'desc', 'version', 'filename',
            'inode', 'notes', 'format'
        ]

    def _format_macb(self, record):
        macb_flags = []
        if 'mtime' in record:
            macb_flags.append('M')
        if 'atime' in record:
            macb_flags.append('A')
        if 'ctime' in record:
            macb_flags.append('C')
        if 'crtime' in record:
            macb_flags.append('B')
        return ''.join(macb_flags)

    def _format_record(self, record):
        date = datetime.utcfromtimestamp(record['timestamp']).strftime('%Y-%m-%d')
        time = datetime.utcfromtimestamp(record['timestamp']).strftime('%H:%M:%S')
        timezone = record.get('timezone', 'UTC')
        macb = self._format_macb(record)
        source = record.get('source', 'FILE')
        sourcetype = record.get('sourcetype', 'NTFS')
        event_type = record.get('type', 'File Modified')
        user = record.get('user', 'Unknown')
        host = record.get('host', 'localhost')
        short_desc = record.get('short_desc', '')
        description = record.get('description', '')
        version = record.get('version', '1.0')
        filename = record.get('filename', '')
        inode = str(record.get('inode', '0'))
        notes = record.get('notes', '')
        event_format = record.get('format', 'l2t_csv')

        return {
            'date': date,
            'time': time,
            'timezone': timezone,
            'MACB': macb,
            'source': source,
            'sourcetype': sourcetype,
            'type': event_type,
            'user': user,
            'host': host,
            'short': short_desc,
            'desc': description,
            'version': version,
            'filename': filename,
            'inode': inode,
            'notes': notes,
            'format': event_format
        }

    def write_records(self, records):
        with open(self.output_file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fields)
            writer.writeheader()
            for record in records:
                formatted_record = self._format_record(record)
                writer.writerow(formatted_record)
