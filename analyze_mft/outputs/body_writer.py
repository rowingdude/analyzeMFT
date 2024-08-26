import os
from typing import Dict, Any

class BodyFileWriter:
    def __init__(self, options: Any, file_handler: Any):
        self.options = options
        self.file_handler = file_handler

    async def write_records(self, mft: Dict[int, Dict[str, Any]]):
        for record in mft.values():
            body_record = await self._format_record(record)
            await self.file_handler.write_body(body_record + '\n')

    async def _format_record(self, record: Dict[str, Any]) -> str:
        md5 = record.get('md5', '0')
        name = record.get('filename', '')
        if self.options.bodyfull:
            name = record.get('full_path', name)
        inode = str(record.get('recordnum', '0'))
        mode = await self._format_mode_as_string(record.get('mode', 0))
        uid = str(record.get('uid', '0'))
        gid = str(record.get('gid', '0'))
        size = str(record.get('size', '0'))
        atime = str(record.get('si', {}).get('atime', '0'))
        mtime = str(record.get('si', {}).get('mtime', '0'))
        ctime = str(record.get('si', {}).get('ctime', '0'))
        crtime = str(record.get('si', {}).get('crtime', '0'))

        return f"{md5}|{name}|{inode}|{mode}|{uid}|{gid}|{size}|{atime}|{mtime}|{ctime}|{crtime}"

    async def _format_mode_as_string(self, mode: int) -> str:
        is_dir = 'd' if os.path.isdir(str(mode)) else '-'
        perm = ''
        for who in ('USR', 'GRP', 'OTH'):
            for what in ('R', 'W', 'X'):
                perm += (who + what) in os.popen(f'stat -c %A {mode}').read()[-4:] and what.lower() or '-'
        return is_dir + perm