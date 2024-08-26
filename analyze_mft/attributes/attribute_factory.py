from typing import Type
from analyze_mft.constants import *
from analyze_mft.attributes.attribute_classes import *
from analyze_mft.attributes.base_attribute import BaseAttribute

class AttributeFactory:
    @staticmethod
    def create_attribute(attr_type: int, raw_data: bytes) -> BaseAttribute:
        attribute_classes = {
            STANDARD_INFORMATION: StandardInformation,
            FILE_NAME: FileName,
            OBJECT_ID: ObjectId,
            DATA: Data,
            INDEX_ROOT: IndexRoot,
            INDEX_ALLOCATION: IndexAllocation,
            BITMAP: Bitmap,
            REPARSE_POINT: ReparsePoint,
            EA_INFORMATION: EAInformation,
            EA: EA,
            PROPERTY_SET: PropertySet,
            LOGGED_UTILITY_STREAM: LoggedUtilityStream
        }
        
        attr_class = attribute_classes.get(attr_type, UnknownAttribute)
        return attr_class(
            type=attr_type,
            name=ATTRIBUTE_NAMES.get(attr_type, "Unknown"),
            raw_data=raw_data
        )