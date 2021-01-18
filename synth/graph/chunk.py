from typing import Iterable, List, Optional

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

    def _basic_types(self, tp: Type) -> Iterable[str]:
        if isinstance(tp, SimpleTypeNode):
            yield tp.core
        elif isinstance(tp, PointerTypeNode):
            yield from self._basic_types(tp.base)
        elif isinstance(tp, ArrayTypeNode):
            yield from self._basic_types(tp.base)
        elif isinstance(tp, FuncTypeNode):
            yield from self._basic_types(tp.ret)
            for arg in tp.args:
                yield from self._basic_types(arg)
        else:
            raise RuntimeError("invalid variable type")

    def basic_types(self) -> Iterable[str]:
        return self._basic_types(self.vtype)


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
        self.constraint = ChunkConstraint() if constraint is None else constraint

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


def merge_chunks(first: Chunk, second: Chunk) -> Chunk:
    return Chunk(
        [*first.variables, *second.variables], first.constraint.join(second.constraint)
    )
