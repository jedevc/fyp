from typing import TYPE_CHECKING, Iterable, List, Optional, Union, overload

from ..builtins import types
from ..node import (
    ArrayTypeNode,
    FuncTypeNode,
    PointerTypeNode,
    SimpleTypeNode,
    TypeNode,
)

if TYPE_CHECKING:
    from .block import Expression


class ChunkVariable:
    def __init__(
        self,
        name: str,
        vtype: Optional[TypeNode],
        chunk: Optional["Chunk"],
        initial: Optional["Expression"] = None,
    ):
        self.name = name
        self.vtype = vtype
        self.chunk = chunk
        self.initial = initial

    def _typestr(self, tp: TypeNode) -> str:
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

    def _typenamestr(self, name: str, tp: TypeNode) -> str:
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
        if self.vtype is None:
            return f"void {self.name}"

        return self._typenamestr(self.name, self.vtype)

    def typestr(self) -> str:
        if self.vtype is None:
            return "void"

        return self._typestr(self.vtype)

    def _basic_types(self, tp: TypeNode) -> Iterable[str]:
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
        if self.vtype is None:
            return iter(())

        return self._basic_types(self.vtype)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.typename()}>"


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

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} eof={self.eof}>"


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

    def add_variable(self, variable: ChunkVariable):
        if variable.name in self._table:
            raise KeyError("variable already exists in chunk")

        self._vars.append(variable)
        self._table[variable.name] = len(self._vars) - 1

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

    def __contains__(self, var: Union[str, ChunkVariable]) -> bool:
        if isinstance(var, str):
            return var in self._table
        else:
            return var in self._vars


@overload
def merge_chunks(first: Optional[Chunk], second: Chunk) -> Chunk:
    ...


@overload
def merge_chunks(first: Chunk, second: Optional[Chunk]) -> Chunk:
    ...


def merge_chunks(first: Optional[Chunk], second: Optional[Chunk]) -> Chunk:
    if first is None:
        assert second is not None
        return second
    if second is None:
        assert first is not None
        return first

    return Chunk(
        [*first.variables, *second.variables], first.constraint.join(second.constraint)
    )
