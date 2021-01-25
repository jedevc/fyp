from typing import List, Optional, Union

from ..builtins.types import METAS, MetaType, MetaTypeGraph
from .base import Node, X
from .visitor import Visitor

TypeNode = Union[
    "UnknownTypeNode",
    "SimpleTypeNode",
    "MetaTypeNode",
    "PointerTypeNode",
    "ArrayTypeNode",
    "FuncTypeNode",
]


class UnknownTypeNode(Node):
    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_type_unknown(self)

    def __repr__(self) -> str:
        return "<UnknownTypeNode>"


class SimpleTypeNode(Node):
    def __init__(self, core: str):
        super().__init__()
        self.core = core

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_type_simple(self)

    @property
    def meta(self) -> MetaType:
        return METAS.get(self.core, MetaType.All)

    def __repr__(self) -> str:
        return f"<SimpleTypeNode {self.core}>"


class MetaTypeNode(Node):
    def __init__(self, meta: MetaType):
        super().__init__()
        self.meta = meta

    def accept(self, visitor: Visitor[X]) -> X:
        raise NotImplementedError()

    def __repr__(self) -> str:
        return f"<MetaTypeNode {self.meta}>"


class PointerTypeNode(Node):
    def __init__(self, base: TypeNode):
        super().__init__()
        self.base = base

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_type_pointer(self)

    def __repr__(self) -> str:
        return f"<PointerTypeNode *{self.base}>"


class ArrayTypeNode(Node):
    def __init__(self, base: TypeNode, size: Optional[int]):
        super().__init__()
        self.base = base
        self.size = size

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_type_array(self)

    def __repr__(self) -> str:
        return f"<ArrayTypeNode []{self.base}>"


class FuncTypeNode(Node):
    def __init__(self, ret: TypeNode, args: List[TypeNode]):
        super().__init__()
        self.ret = ret
        self.args = args

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_type_func(self)

    def __repr__(self) -> str:
        args = ", ".join(repr(arg) for arg in self.args)
        return f"<FuncTypeNode ({args}) -> {self.ret}>"


def metatype_is_reachable(start: MetaType, destination: MetaType) -> bool:
    if start == destination:
        return True

    stack = [start]
    while len(stack) > 0:
        expand = stack.pop()
        for conn in MetaTypeGraph[expand]:
            if conn == destination:
                return True
            elif conn not in stack:
                # avoid infinite recursion
                continue

            stack.append(conn)

    return False


def type_check(left: TypeNode, right: TypeNode) -> bool:
    if isinstance(left, UnknownTypeNode) or isinstance(right, UnknownTypeNode):
        return True
    elif isinstance(left, SimpleTypeNode) and isinstance(right, SimpleTypeNode):
        return left.core == right.core
    elif isinstance(left, PointerTypeNode) and isinstance(right, PointerTypeNode):
        return type_check(left.base, right.base)
    elif isinstance(left, ArrayTypeNode) and isinstance(right, ArrayTypeNode):
        return type_check(left.base, right.base)
    elif isinstance(left, FuncTypeNode) and isinstance(right, FuncTypeNode):
        if len(left.args) != len(right.args):
            return False

        success = type_check(left.ret, right.ret)
        for i in range(len(left.args)):
            success &= type_check(left.args[i], right.args[i])
            if not success:
                # early exit
                break

        return success
    else:
        return False
