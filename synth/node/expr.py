from typing import List, Union

from .base import Node, X
from .visitor import Visitor

Lvalue = Union["VariableNode", "ArrayNode", "DerefNode"]
Expression = Union["FunctionNode", "ValueNode", "RefNode", Lvalue]


class FunctionNode(Node):
    def __init__(self, target: str, arguments: List[Expression]):
        super().__init__()
        self.target = target
        self.arguments = arguments

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_function(self)


class RefNode(Node):
    def __init__(self, target: Lvalue):
        super().__init__()
        self.target = target

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_ref(self)


class DerefNode(Node):
    def __init__(self, target: Expression):
        super().__init__()
        self.target = target

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_deref(self)


class VariableNode(Node):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_variable(self)


class ArrayNode(Node):
    def __init__(self, target: Expression, index: Expression):
        super().__init__()
        self.target = target
        self.index = index

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_array(self)


class ValueNode(Node):
    def __init__(self, value: Union[str, int]):
        super().__init__()
        self.value = value

    def is_str(self) -> bool:
        return isinstance(self.value, str)

    def is_int(self) -> bool:
        return isinstance(self.value, int)

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_value(self)
