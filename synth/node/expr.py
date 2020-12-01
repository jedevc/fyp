from enum import Enum, unique
from typing import List, Union

from .base import Node, X
from .visitor import Visitor

Lvalue = Union["VariableNode", "ArrayNode", "DerefNode"]
Expression = Union[
    "BinaryOperationNode", "FunctionNode", "ValueNode", "RefNode", Lvalue
]


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


class VariableNode(Node):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_variable(self)


class DerefNode(Node):
    def __init__(self, target: Expression):
        super().__init__()
        self.target = target

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_deref(self)


class ArrayNode(Node):
    def __init__(self, target: Expression, index: Expression):
        super().__init__()
        self.target = target
        self.index = index

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_array(self)


class RefNode(Node):
    def __init__(self, target: Lvalue):
        super().__init__()
        self.target = target

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_ref(self)


@unique
class Operator(Enum):
    Add = 1
    Subtract = 2
    Multiply = 3
    Divide = 4

    Eq = 5
    Gt = 6
    Gte = 7
    Lt = 8
    Lte = 9


class BinaryOperationNode(Node):
    def __init__(self, op: Operator, left: Expression, right: Expression):
        super().__init__()
        self.op = op
        self.left = left
        self.right = right

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_binary(self)


class FunctionNode(Node):
    def __init__(self, target: str, arguments: List[Expression]):
        super().__init__()
        self.target = target
        self.arguments = arguments

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_function(self)
