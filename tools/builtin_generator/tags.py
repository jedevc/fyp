class Tag:
    def __init__(self, spec):
        self.name = spec.get("name")
        self.path = spec.get("path")
        self.pattern = spec.get("pattern")
        self.signature = spec.get("signature")
        self.typeref = spec.get("typeref")
        self.kind = spec.get("kind")

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
