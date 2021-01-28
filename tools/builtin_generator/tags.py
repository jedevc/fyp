from enum import Enum, unique
from typing import Any, Dict


class Tag:
    def __init__(self, spec: Dict[str, str]):
        self.name = spec.get("name")
        self.pattern = spec.get("pattern")
        self.kind = TagKind(spec.get("kind"))
        self.path = spec.get("path")

        if "signature" in spec:
            self.signature = spec["signature"].lstrip("(").rstrip(")").split(",")
        else:
            self.signature = []

        self.typeref = spec.get("typeref", "void").removeprefix("typename:")
        if ":" in self.typeref:
            self.typeref = " ".join(self.typeref.split(":"))

    def asdict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "path": self.path,
            "pattern": self.pattern,
            "signature": self.signature,
            "typeref": self.typeref,
        }


@unique
class TagKind(Enum):
    MACRO = "macro"
    EXTERN = "externvar"
    PROTOTYPE = "prototype"
    FUNCTION = "function"
    TYPEDEF = "typedef"
    UNION = "union"
    STRUCT = "struct"
    ENUM = "enum"
    ENUMERATOR = "enumerator"
    VARIABLE = "variable"

    MEMBER = "member"  # ???
