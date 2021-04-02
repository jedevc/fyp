from typing import TYPE_CHECKING, Iterable, List, Optional, Union, overload

from ..builtins import types
from ..common.error import ConstraintError
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

    def _typenamestr(
        self, tp: TypeNode, original: Optional[str], name: Optional[str]
    ) -> str:
        original = original or ""
        name = name or ""

        if isinstance(tp, SimpleTypeNode):
            return f"{types.TRANSLATIONS[tp.core]} {name}"
        elif isinstance(tp, FuncTypeNode):
            args = ", ".join(self._typenamestr(arg, None, None) for arg in tp.args)
            if name == original:
                assert original
                base = f"{original}({args})"
                return self._typenamestr(tp.ret, base, base)
            else:
                ret = self._typenamestr(tp.ret, None, None)
                return f"{ret} ({name})({args})"
        elif isinstance(tp, PointerTypeNode):
            return self._typenamestr(tp.base, original, f"*{name}")
        elif isinstance(tp, ArrayTypeNode):
            return self._typenamestr(tp.base, original, f"{name}[{tp.size}]")
        else:
            raise RuntimeError("invalid variable type")

    def typename(self) -> str:
        if self.vtype is None:
            return f"void {self.name}"

        return self._typenamestr(self.vtype, self.name, self.name)

    def typestr(self) -> str:
        if self.vtype is None:
            return "void"

        return self._typenamestr(self.vtype, None, None).strip()

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
    def __init__(self, islocal=False, isglobal=False, static=False):
        self.islocal = islocal
        self.isglobal = isglobal
        self.static = static

        self._verify()

    def copy(self) -> "ChunkConstraint":
        return ChunkConstraint(
            islocal=self.islocal, isglobal=self.isglobal, static=self.static
        )

    def merge(self, other: "ChunkConstraint"):
        self.islocal = self.islocal or other.islocal
        self.isglobal = self.isglobal or other.isglobal
        self.static = self.static or other.static

        self._verify()

    def _verify(self):
        if self.islocal and self.isglobal:
            raise ConstraintError("cannot allow local and global constraints")

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} local={self.islocal} global={self.isglobal} static={self.static}>"


class Chunk:
    def __init__(
        self,
        variables: List[ChunkVariable],
        constraint: Optional[ChunkConstraint] = None,
    ):
        self.variables = variables
        self._table = {
            var.name: i
            for i, var in enumerate(variables)
            if not var.name.startswith("_")
        }
        self.constraint = ChunkConstraint() if constraint is None else constraint

    @property
    def varnames(self) -> List[str]:
        return [var.name for var in self.variables]

    def add_variable(self, variable: ChunkVariable):
        if variable.name in self._table:
            raise KeyError("variable already exists in chunk")

        self.variables.append(variable)
        self._table[variable.name] = len(self.variables) - 1

    def rename_variable(self, variable: ChunkVariable, name: str):
        if variable not in self.variables:
            raise KeyError("variable not in chunk")

        idx = self._table[variable.name]

        self._table.pop(variable.name)
        variable.name = name
        self._table[variable.name] = idx

    def remove_variable(self, variable: ChunkVariable):
        if variable.name not in self._table:
            raise KeyError("variable not in chunk table")

        idx = self._table[variable.name]
        target = self.variables[idx]
        if target is not variable:
            raise KeyError("variable does not match")

        self.variables.remove(target)
        self._table.pop(target.name)

    def lookup(self, name: str) -> Optional[ChunkVariable]:
        i = self._table.get(name)
        if i is None:
            return None
        else:
            return self.variables[i]

    def __contains__(self, var: Union[str, ChunkVariable]) -> bool:
        if isinstance(var, str):
            return var in self._table
        else:
            return var in self.variables


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

    constraint = first.constraint.copy()
    constraint.merge(second.constraint)

    return Chunk([*first.variables, *second.variables], constraint)
