#!/usr/bin/env python

# Version 2.1.1
#
# Author: Benjamin Cance (bjc@tdx.li)
# Copyright Benjamin Cance 2024
#
# 2-Aug-24 
# - Updating to current PEP
#
# 12-Aug-24
# - Seperating out functionality into specific files
# - Adding json export 

import json
import logging
from typing import Dict, Any, List
from .mft_utils import decodeMFTmagic, decodeMFTisactive, decodeMFTrecordtype


def mft_to_csv(record: Dict[str, Any], ret_header: bool) -> List[str]:

    try:
        if ret_header:
            return [
            'Record Number', 'Good', 'Active', 'Record type',
            'Sequence Number', 'Parent File Rec. #', 'Parent File Rec. Seq. #',
            'Filename #1', 'Std Info Creation date', 'Std Info Modification date',
            'Std Info Access date', 'Std Info Entry date', 'FN Info Creation date',
            'FN Info Modification date', 'FN Info Access date', 'FN Info Entry date',
            'Object ID', 'Birth Volume ID', 'Birth Object ID', 'Birth Domain ID',
            'Filename #2', 'FN Info Creation date', 'FN Info Modify date',
            'FN Info Access date', 'FN Info Entry date', 'Filename #3', 'FN Info Creation date',
            'FN Info Modify date', 'FN Info Access date', 'FN Info Entry date', 'Filename #4',
            'FN Info Creation date', 'FN Info Modify date', 'FN Info Access date',
            'FN Info Entry date', 'Standard Information', 'Attribute List', 'Filename',
            'Object ID', 'Volume Name', 'Volume Info', 'Data', 'Index Root',
            'Index Allocation', 'Bitmap', 'Reparse Point', 'EA Information', 'EA',
            'Property Set', 'Logged Utility Stream', 'Log/Notes', 'STF FN Shift', 'uSec Zero'
            ]

        if 'baad' in record:
            return [str(record['recordnum']), "BAAD MFT Record"]

        csv_string = [
            record['recordnum'],
            decodeMFTmagic(record),
            decodeMFTisactive(record),
            decodeMFTrecordtype(record),
            str(record['seq'])
        ]

        if 'corrupt' in record:
            return csv_string + [str(record['recordnum']), "Corrupt", "Corrupt", "Corrupt MFT Record"]

        tmp_string = ["%d" % record['seq']]
        csv_string.extend(tmp_string)

        if record['fncnt'] > 0:
            csv_string.extend([str(record['fn',0]['par_ref']), str(record['fn',0]['par_seq'])])
        else:
            csv_string.extend(['NoParent', 'NoParent'])

        if record['fncnt'] > 0 and 'si' in record:
            
            filenameBuffer = [record['filename'],  str(record['si']['crtime'].dtstr),
                    record['si']['mtime'].dtstr,    record['si']['atime'].dtstr, record['si']['ctime'].dtstr,
                    record['fn',0]['crtime'].dtstr, record['fn',0]['mtime'].dtstr,
                    record['fn',0]['atime'].dtstr,  record['fn',0]['ctime'].dtstr]
        elif 'si' in record:

            filenameBuffer = ['NoFNRecord', str(record['si']['crtime'].dtstr),
                    record['si']['mtime'].dtstr, record['si']['atime'].dtstr, record['si']['ctime'].dtstr,
                    'NoFNRecord', 'NoFNRecord', 'NoFNRecord','NoFNRecord']
        else:

            filenameBuffer = ['NoFNRecord', 'NoSIRecord', 'NoSIRecord', 'NoSIRecord', 'NoSIRecord',
                            'NoFNRecord', 'NoFNRecord', 'NoFNRecord', 'NoFNRecord']


        csv_string.extend(filenameBuffer)

        if 'objid' in record:
            objidBuffer = [record['objid']['objid'], record['objid']['orig_volid'],
                        record['objid']['orig_objid'], record['objid']['orig_domid']]
        else:
            objidBuffer = ['','','','']

        csv_string.extend(objidBuffer)

        for i in range(1, record['fncnt']):
            filenameBuffer = [record['fn',i]['name'], record['fn',i]['crtime'].dtstr, record['fn',i]['mtime'].dtstr,
                    record['fn',i]['atime'].dtstr, record['fn',i]['ctime'].dtstr]
            csv_string.extend(filenameBuffer)
            filenameBuffer = ''

        if record['fncnt'] < 2:
            tmp_string = ['','','','','','','','','','','','','','','']
        elif record['fncnt'] == 2:
            tmp_string = ['','','','','','','','','','']
        elif record['fncnt'] == 3:
            tmp_string = ['','','','','']

        csv_string.extend(tmp_string)

        
        attributes = ['si', 'al', 'objid', 'volname', 'volinfo', 'data', 'indexroot', 
                    'indexallocation', 'bitmap', 'reparse', 'eainfo', 'ea', 
                    'propertyset', 'loggedutility']

        csv_string.extend(
            ['True' if attr in record else 'False' for attr in attributes]
        )

        csv_string.append('True' if record.get('fncnt', 0) > 0 else 'False')

        if 'notes' in record:                        # Log of abnormal activity related to this record
            csv_string.append(record['notes'])
        else:
            csv_string.append('None')
            record['notes'] = ''

        if 'stf-fn-shift' in record:
            csv_string.append('Y')
        else:
            csv_string.append('N')

        if 'usec-zero' in record:
            csv_string.append('Y')
        else:
            csv_string.append('N')

        return csv_string
    
    except KeyError as e:

        logging.error(f"Missing key in record: {e}")
        return []

def mft_to_body(record: Dict[str, Any], full: bool, std: bool) -> str:
    try:

        if record['fncnt'] > 0:

            if full == True: # Use full path
                name = record['filename']
            else:
                name = record['fn',0]['name']

            if std == True:     # Use STD_INFO
                rec_bodyfile = ("%s|%s|%s|%s|%s|%s|%s|%d|%d|%d|%d\n" %
                            ('0',name,'0','0','0','0',
                            int(record['fn',0]['real_fsize']),
                            int(record['si']['atime'].unixtime),  # was str ....
                            int(record['si']['mtime'].unixtime),
                            int(record['si']['ctime'].unixtime),
                            int(record['si']['ctime'].unixtime)))
            else:               # Use FN
                rec_bodyfile = ("%s|%s|%s|%s|%s|%s|%s|%d|%d|%d|%d\n" %
                            ('0',name,'0','0','0','0',
                            int(record['fn',0]['real_fsize']),
                            int(record['fn',0]['atime'].unixtime),
                            int(record['fn',0]['mtime'].unixtime),
                            int(record['fn',0]['ctime'].unixtime),
                            int(record['fn',0]['crtime'].unixtime)))

        else:
            if 'si' in record:
                rec_bodyfile = ("%s|%s|%s|%s|%s|%s|%s|%d|%d|%d|%d\n" %
                            ('0','No FN Record','0','0','0','0', '0',
                            int(record['si']['atime'].unixtime),  # was str ....
                            int(record['si']['mtime'].unixtime),
                            int(record['si']['ctime'].unixtime),
                            int(record['si']['ctime'].unixtime)))
            else:
                rec_bodyfile = ("%s|%s|%s|%s|%s|%s|%s|%d|%d|%d|%d\n" %
                                    ('0','Corrupt Record','0','0','0','0', '0',0, 0, 0, 0))

        return rec_bodyfile
    
    except KeyError as e:

        logging.error(f"Missing key in record: {e}")
        return ""

def mft_to_l2t(record: Dict[str, Any]) -> str:
    try:
    
        if record['fncnt'] > 0:
            for i in ('atime', 'mtime', 'ctime', 'crtime'):
                (date,time) = record['fn',0][i].dtstr.split(' ')

                if i == 'atime':
                    type_str = '$FN [.A..] time'
                    macb_str = '.A..'
                if i == 'mtime':
                    type_str = '$FN [M...] time'
                    macb_str = 'M...'
                if i == 'ctime':
                    type_str = '$FN [..C.] time'
                    macb_str = '..C.'
                if i == 'crtime':
                    type_str = '$FN [...B] time'
                    macb_str = '...B'

                csv_string = ("%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s\n" %
                    (date, time, 'TZ', macb_str, 'FILE', 'NTFS $MFT', type_str, 'user', 'host', record['filename'], 'desc',
                    'version', record['filename'], record['seq'], record['notes'], 'format', 'extra'))

        elif 'si' in record:
            for i in ('atime', 'mtime', 'ctime', 'crtime'):
                (date,time) = record['si'][i].dtstr.split(' ')

                if i == 'atime':
                    type_str = '$SI [.A..] time'
                    macb_str = '.A..'
                if i == 'mtime':
                    type_str = '$SI [M...] time'
                    macb_str = 'M...'
                if i == 'ctime':
                    type_str = '$SI [..C.] time'
                    macb_str = '..C.'
                if i == 'crtime':
                    type_str = '$SI [...B] time'
                    macb_str = '...B'

                csv_string = ("%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s\n" %
                    (date, time, 'TZ', macb_str, 'FILE', 'NTFS $MFT', type_str, 'user', 'host', record['filename'], 'desc',
                    'version', record['filename'], record['seq'], record['notes'], 'format', 'extra'))

        else:
            csv_string = ("%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s\n" %
                    ('-', '-', 'TZ', 'unknown time', 'FILE', 'NTFS $MFT', 'unknown time', 'user', 'host', 'Corrupt Record', 'desc',
                    'version', 'NoFNRecord', record['seq'], '-', 'format', 'extra'))

        return csv_string
    
    except KeyError as e:
        logging.error(f"Missing key in record: {e}")
        return ""
    
def mft_to_json(record: Dict[str, Any]) -> str:

    try:

        for key, value in record.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if hasattr(sub_value, 'dtstr'):
                        value[sub_key] = sub_value.dtstr
        return json.dumps(record, indent=2)
    
    except (TypeError, ValueError) as e:

        logging.error(f"Error converting record to JSON: {e}")
        return "{}"