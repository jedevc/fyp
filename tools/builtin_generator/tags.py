from enum import Enum, unique
from typing import Any, Dict


class Tag:
    def __init__(self, spec: Dict[str, str]):
        self.name = spec["name"]
        self.pattern = spec["pattern"]
        self.kind = TagKind(spec["kind"])
        self.path = spec["path"]

        if "signature" in spec:
            sig = spec["signature"]
            if sig.startswith("("):
                sig = sig.removeprefix("(")
                sig = sig.removesuffix(")")
            self.signature = sig
        else:
            self.signature = ""

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
    CLASS = "class"
    UNION = "union"
    STRUCT = "struct"
    ENUM = "enum"
    ENUMERATOR = "enumerator"
    VARIABLE = "variable"
    LOCAL = "local"

    MEMBER = "member"  # ???
