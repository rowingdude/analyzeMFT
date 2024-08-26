from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class BaseAttribute(ABC):
    type: int
    name: str
    raw_data: bytes

    @abstractmethod
    async def parse(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def validate(self) -> bool:
        pass