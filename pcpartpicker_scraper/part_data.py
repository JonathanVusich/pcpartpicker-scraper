from dataclasses import dataclass
from typing import List


@dataclass
class PartData:
    brands: List[str]
    tokens: List[List[str]]
