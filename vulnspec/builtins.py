import json
from pathlib import Path
from typing import NewType

from .common.data import data_path

BUILTINS_PATH = data_path("builtins")


class BuiltinBase:
    def __init__(self, path: Path):
        with path.open() as f:
            self._data = json.load(f)


class Functions(BuiltinBase):
    def __init__(self, path: Path):
        super().__init__(path)

        self.SIGNATURES = self._data["signatures"]
        self.TRANSLATIONS = self._data["translations"]
        self.PATHS = self._data["paths"]


class Variables(BuiltinBase):
    def __init__(self, path: Path):
        super().__init__(path)

        self.TYPES = self._data["types"]
        self.TRANSLATIONS = self._data["translations"]
        self.PATHS = self._data["paths"]


MetaType = NewType("MetaType", str)


class Types(BuiltinBase):
    def __init__(self, path: Path):
        super().__init__(path)

        self.METAS = self._data["metas"]
        self.META_GRAPH = self._data["meta_graph"]
        self.META_PARENTS = self._data["meta_parents"]

        self.TRANSLATIONS = self._data["translations"]
        self.PATHS = self._data["paths"]

    def meta(self, tp: str) -> MetaType:
        if tp in self.METAS:
            return MetaType(tp)
        else:
            raise KeyError(tp)


functions = Functions(BUILTINS_PATH / "functions.json")
variables = Variables(BUILTINS_PATH / "variables.json")
types = Types(BUILTINS_PATH / "types.json")


class MetaTypes:
    Any = types.meta("any")
    Pointer = types.meta("pointer")
    Void = types.meta("void")
    Boolean = types.meta("boolean")
    Integral = types.meta("integral")
    Floating = types.meta("floating")
    Complex = types.meta("complex")
