from typing import List, Optional, Union

from ..builtins import types
from ..node import ArrayTypeNode, FuncTypeNode, PointerTypeNode, SimpleTypeNode, Type


class ChunkVariable:
    def __init__(self, name: str, vtype: Type):
        self.name = name
        self.vtype = vtype

    def _typestr(self, tp: Type) -> str:
        if isinstance(tp, SimpleTypeNode):
            return types.TRANSLATIONS[tp.core]
        elif isinstance(tp, PointerTypeNode):
            return f"*{self._typestr(tp.base)}"
        elif isinstance(tp, ArrayTypeNode):
            return f"{self._typestr(tp.base)}[{tp.size}]"
        elif isinstance(tp, FuncTypeNode):
            args = ", ".join(self._typestr(arg) for arg in tp.args)
            ret = self._typestr(tp.ret)
            return f"{ret} (*)({args})"
        else:
            raise RuntimeError("invalid variable type")

    def _typenamestr(self, name: str, tp: Type) -> str:
        if isinstance(tp, SimpleTypeNode):
            return f"{types.TRANSLATIONS[tp.core]} {name}"
        elif isinstance(tp, PointerTypeNode):
            return self._typenamestr(f"*{name}", tp.base)
        elif isinstance(tp, ArrayTypeNode):
            return self._typenamestr(f"{name}[{tp.size}]", tp.base)
        elif isinstance(tp, FuncTypeNode):
            args = ", ".join(self._typestr(arg) for arg in tp.args)
            ret = self._typestr(tp.ret)
            return f"{ret} (*{name})({args})"
        else:
            raise RuntimeError("invalid variable type")

    def typename(self) -> str:
        return self._typenamestr(self.name, self.vtype)


class ChunkConstraint:
    def __init__(self, eof=False):
        self.eof = eof

    def join(self, other) -> "ChunkConstraint":
        return ChunkConstraint(
            eof=self.eof or other.eof,
        )

    @property
    def empty(self) -> bool:
        return not self.eof


class Chunk:
    def __init__(
        self,
        variables: List[ChunkVariable],
        constraint: Optional[ChunkConstraint] = None,
    ):
        self._vars = variables
        self._table = {
            var.name: i
            for i, var in enumerate(variables)
            if not var.name.startswith("_")
        }
        self.constraint = constraint

    @property
    def variables(self) -> List[ChunkVariable]:
        return self._vars

    def lookup(self, name: str) -> Optional[ChunkVariable]:
        if name.startswith("_"):
            raise KeyError("cannot lookup hidden variable")

        i = self._table.get(name)
        if i is None:
            return None
        else:
            return self._vars[i]


class ChunkSet(Chunk):
    def __init__(self, externs: List[ChunkVariable], chunks: List[Chunk]):
        super().__init__(externs)
        self.chunks = chunks

    @property
    def externs(self) -> List[ChunkVariable]:
        return super().variables

    @property
    def variables(self) -> List[ChunkVariable]:
        result = []
        for chunk in self.chunks:
            result.extend(chunk.variables)
        return result

    def find(self, name: str) -> Union[Chunk, "ChunkSet", None]:
        if name in self._table:
            return self

        for chunk in self.chunks:
            if chunk.lookup(name):
                return chunk

        return None
