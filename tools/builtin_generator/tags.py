class Tag:
    def __init__(self, spec):
        self.name = spec.get("name")
        self.path = spec.get("path")
        self.pattern = spec.get("pattern")
        self.kind = spec.get("kind")

        if "signature" in spec:
            self.signature = spec["signature"].lstrip("(").rstrip(")").split(",")
        else:
            self.signature = None

        self.typeref = spec.get("typeref", "void").removeprefix("typename:")
        if ":" in self.typeref:
            self.typeref = " ".join(self.typeref.split(":"))

    def asdict(self):
        return {
            "name": self.name,
            "kind": self.kind,
            "path": self.path,
            "pattern": self.pattern,
            "signature": self.signature,
            "typeref": self.typeref,
        }


class TagKind:
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
