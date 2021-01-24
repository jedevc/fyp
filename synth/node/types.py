from typing import List, Optional, Union

from .base import Node, X
from .visitor import Visitor

TypeNode = Union[
    "UnknownTypeNode",
    "SimpleTypeNode",
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

    def __repr__(self) -> str:
        return f"<SimpleTypeNode {self.core}>"


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
