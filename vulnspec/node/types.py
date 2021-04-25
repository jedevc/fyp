from typing import List, Union

from ..builtins import MetaType, MetaTypes, types
from .base import Node, X
from .value import IntValueNode, TemplateValueNode
from .visitor import Visitor

TypeNode = Union[
    "SimpleTypeNode",
    "MetaTypeNode",
    "PointerTypeNode",
    "ArrayTypeNode",
    "FuncTypeNode",
]


class SimpleTypeNode(Node):
    def __init__(self, core: str):
        super().__init__()
        self.core = core

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_type_simple(self)

    @property
    def meta(self) -> MetaType:
        return types.META_PARENTS.get(self.core, MetaTypes.Any)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.core}>"


class MetaTypeNode(Node):
    def __init__(self, core: MetaType):
        super().__init__()
        self.core = core

    def accept(self, visitor: Visitor[X]) -> X:
        # This is intentionally not implemented - meta types are a constraint
        # generted during type checking, so it will never appear in the AST.
        raise NotImplementedError()

    @property
    def meta(self) -> MetaType:
        return self.core

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.core}>"


class PointerTypeNode(Node):
    def __init__(self, base: TypeNode):
        super().__init__()
        self.base = base

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_type_pointer(self)

    @property
    def meta(self) -> MetaType:
        return types.meta("pointer")

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.base}>"


class ArrayTypeNode(Node):
    def __init__(
        self, base: TypeNode, size: Union[None, IntValueNode, TemplateValueNode]
    ):
        super().__init__()
        self.base = base
        self.size = size

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_type_array(self)

    @property
    def meta(self) -> MetaType:
        return MetaTypes.Pointer

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.base}>"


class FuncTypeNode(Node):
    def __init__(self, ret: TypeNode, args: List[TypeNode], variadic: bool = False):
        super().__init__()
        self.ret = ret
        self.args = args
        self.variadic = variadic

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_type_func(self)

    @property
    def meta(self) -> MetaType:
        return MetaTypes.Void

    def __repr__(self) -> str:
        args = ", ".join(repr(arg) for arg in self.args)
        return f"<{self.__class__.__name__} ({args}) -> {self.ret}>"


def metatype_is_reachable(start: MetaType, destination: MetaType) -> bool:
    if start == destination:
        return True
    if MetaTypes.Any in (start, destination):
        # NOTE: special exception!
        return True

    stack = [start]
    while len(stack) > 0:
        expand = stack.pop()
        for conn in types.META_GRAPH[expand]:
            if conn in stack:
                continue

            if conn == destination:
                return True

            stack.append(conn)

    return False


def type_check(ctx: TypeNode, tp: TypeNode, strict: bool = False) -> bool:
    if isinstance(ctx, MetaTypeNode) or isinstance(tp, MetaTypeNode):
        return metatype_is_reachable(tp.meta, ctx.meta)
    elif isinstance(ctx, SimpleTypeNode) and isinstance(tp, SimpleTypeNode):
        lcore = ctx.core.split("@")[0]
        rcore = tp.core.split("@")[0]
        if lcore == rcore:
            return True
    elif isinstance(ctx, (ArrayTypeNode, PointerTypeNode)) and isinstance(
        tp, (ArrayTypeNode, PointerTypeNode)
    ):
        return type_check(ctx.base, tp.base, strict=True)
    elif isinstance(ctx, FuncTypeNode) and isinstance(tp, FuncTypeNode):
        if len(ctx.args) != len(tp.args):
            return False
        if not type_check(ctx.ret, tp.ret, strict=strict):
            return False
        return all(type_check(la, ra, strict=True) for la, ra in zip(ctx.args, tp.args))

    return not strict and metatype_is_reachable(tp.meta, ctx.meta)
