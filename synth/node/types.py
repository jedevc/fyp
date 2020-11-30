from typing import List, Union

from .base import Node, X
from .visitor import Visitor

Type = Union["SimpleTypeNode", "PointerTypeNode", "ArrayTypeNode", "FuncTypeNode"]


class SimpleTypeNode(Node):
    def __init__(self, core: str):
        super().__init__()
        self.core = core

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_type_simple(self)


class PointerTypeNode(Node):
    def __init__(self, base: Type):
        super().__init__()
        self.base = base

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_type_pointer(self)


class ArrayTypeNode(Node):
    def __init__(self, base: Type, size: int):
        super().__init__()
        self.base = base
        self.size = size

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_type_array(self)


class FuncTypeNode(Node):
    def __init__(self, ret: Type, args: List[Type]):
        super().__init__()
        self.ret = ret
        self.args = args

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_type_func(self)