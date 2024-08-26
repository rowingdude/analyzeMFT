import struct
from typing import Any, Dict
from analyze_mft.attributes.base_attribute import BaseAttribute
from analyze_mft.utilities.windows_time import WindowsTime


class AttributeList(BaseAttribute):
    async def parse(self) -> Dict[str, Any]:
        if not self.validate():
            raise ValueError("Invalid Attribute List attribute")

        offset = 0
        attributes = []

        while offset < len(self.raw_data):
            if len(self.raw_data) < offset + 12:
                break

            attr_type = struct.unpack("<H", self.raw_data[offset:offset + 2])[0]
            attr_length = struct.unpack("<I", self.raw_data[offset + 4:offset + 8])[0]
            attr_name_length = struct.unpack("<H", self.raw_data[offset + 8:offset + 10])[0]
            attr_name_offset = struct.unpack("<H", self.raw_data[offset + 10:offset + 12])[0]

            if len(self.raw_data) < offset + attr_length:
                break

            attributes.append({
                'type': attr_type,
                'length': attr_length,
                'name_length': attr_name_length,
                'name_offset': attr_name_offset,
                'attribute_data': self.raw_data[offset:offset + attr_length].hex()
            })

            offset += attr_length

        return {
            'attributes': attributes
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type,
            'name': self.name,
            'data': self.parse()
        }

    def validate(self) -> bool:
        return len(self.raw_data) >= 12 

class StandardInformation(BaseAttribute):
    async def parse(self) -> Dict[str, Any]:
        if not self.validate():
            raise ValueError("Invalid Standard Information attribute")

        return {
            'crtime': WindowsTime(struct.unpack("<Q", self.raw_data[:8])[0]),
            'mtime': WindowsTime(struct.unpack("<Q", self.raw_data[8:16])[0]),
            'ctime': WindowsTime(struct.unpack("<Q", self.raw_data[16:24])[0]),
            'atime': WindowsTime(struct.unpack("<Q", self.raw_data[24:32])[0]),
            'dos_flags': struct.unpack("<I", self.raw_data[32:36])[0],
            'max_versions': struct.unpack("<I", self.raw_data[36:40])[0],
            'version': struct.unpack("<I", self.raw_data[40:44])[0],
            'class_id': struct.unpack("<I", self.raw_data[44:48])[0],
            'owner_id': struct.unpack("<I", self.raw_data[48:52])[0],
            'security_id': struct.unpack("<I", self.raw_data[52:56])[0],
            'quota_charged': struct.unpack("<Q", self.raw_data[56:64])[0],
            'usn': struct.unpack("<Q", self.raw_data[64:72])[0]
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type,
            'name': self.name,
            'data': self.parse()
        }

    def validate(self) -> bool:
        return len(self.raw_data) >= 72

class DataRuns(BaseAttribute):
    async def parse(self) -> Dict[str, Any]:
        if not self.validate():
            raise ValueError("Invalid Data Runs attribute")

        # Basic idea, need to add to this
        runs = []
        offset = 0
        while offset < len(self.raw_data):
            run_length = struct.unpack("<H", self.raw_data[offset:offset+2])[0]
            run_offset = struct.unpack("<H", self.raw_data[offset+2:offset+4])[0]
            runs.append({'length': run_length, 'offset': run_offset})
            offset += 4
        
        return {
            'runs': runs
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type,
            'name': self.name,
            'data': self.parse()
        }

    def validate(self) -> bool:
        return len(self.raw_data) >= 8  

class FileName(BaseAttribute):
    async def parse(self) -> Dict[str, Any]:
        if not self.validate():
            raise ValueError("Invalid File Name attribute")

        name_length = struct.unpack("B", self.raw_data[64:65])[0]
        name_offset = 66
        
        return {
            'parent_ref': struct.unpack("<Q", self.raw_data[:8])[0],
            'crtime': WindowsTime(struct.unpack("<Q", self.raw_data[8:16])[0]),
            'mtime': WindowsTime(struct.unpack("<Q", self.raw_data[16:24])[0]),
            'ctime': WindowsTime(struct.unpack("<Q", self.raw_data[24:32])[0]),
            'atime': WindowsTime(struct.unpack("<Q", self.raw_data[32:40])[0]),
            'alloc_size': struct.unpack("<Q", self.raw_data[40:48])[0],
            'real_size': struct.unpack("<Q", self.raw_data[48:56])[0],
            'flags': struct.unpack("<I", self.raw_data[56:60])[0],
            'reparse': struct.unpack("<I", self.raw_data[60:64])[0],
            'name_length': name_length,
            'namespace': struct.unpack("B", self.raw_data[65:66])[0],
            'name': self.raw_data[name_offset:name_offset + name_length * 2].decode('utf-16-le')
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type,
            'name': self.name,
            'data': self.parse()
        }

    def validate(self) -> bool:
        if len(self.raw_data) < 66:
            return False
        name_length = struct.unpack("B", self.raw_data[64:65])[0]
        return len(self.raw_data) >= 66 + name_length * 2

class IndexRoot(BaseAttribute):
    async def parse(self) -> Dict[str, Any]:
        if not self.validate():
            raise ValueError("Invalid Index Root attribute")

        return {
            'type': struct.unpack("<H", self.raw_data[0:2])[0],
            'length': struct.unpack("<I", self.raw_data[2:6])[0],
            'alloc_size': struct.unpack("<I", self.raw_data[6:10])[0],
            'real_size': struct.unpack("<I", self.raw_data[10:14])[0],
            'flags': struct.unpack("<H", self.raw_data[14:16])[0],
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type,
            'name': self.name,
            'data': self.parse()
        }

    def validate(self) -> bool:
        return len(self.raw_data) >= 16

class ObjectId(BaseAttribute):
    async def parse(self) -> Dict[str, Any]:
        if not self.validate():
            raise ValueError("Invalid Object ID attribute")

        return {
            'object_id': self.raw_data[:16].hex(),
            'birth_volume_id': self.raw_data[16:32].hex(),
            'birth_object_id': self.raw_data[32:48].hex(),
            'domain_id': self.raw_data[48:64].hex()
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type,
            'name': self.name,
            'data': self.parse()
        }

    def validate(self) -> bool:
        return len(self.raw_data) >= 64



class UnknownAttribute(BaseAttribute):
    async def parse(self) -> Dict[str, Any]:
        return {'raw_data': self.raw_data.hex()}

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type,
            'name': self.name,
            'data': self.parse()
        }

    def validate(self) -> bool:
        return True  # Always consider unknown attributes as valid