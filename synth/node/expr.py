from enum import Enum, unique
from typing import List, Union

from .base import Node, X
from .visitor import Visitor

LvalueNode = Union["VariableNode", "ArrayNode", "DerefNode", "LiteralNode"]
ExpressionNode = Union[
    "BinaryOperationNode", "FunctionNode", "ValueNode", "RefNode", LvalueNode
]


class ValueNode(Node):
    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_value(self)


class IntValueNode(ValueNode):
    def __init__(self, value: int, base: int):
        super().__init__()
        self.value = value
        self.base = base


class StringValueNode(ValueNode):
    def __init__(self, value: str):
        super().__init__()
        self.value = value


class LiteralNode(Node):
    def __init__(self, content: str):
        super().__init__()
        self.content = content

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_literal(self)


class VariableNode(Node):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_variable(self)


class DerefNode(Node):
    def __init__(self, target: ExpressionNode):
        super().__init__()
        self.target = target

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_deref(self)


class ArrayNode(Node):
    def __init__(self, target: ExpressionNode, index: ExpressionNode):
        super().__init__()
        self.target = target
        self.index = index

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_array(self)


class RefNode(Node):
    def __init__(self, target: LvalueNode):
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
    Neq = 6
    Gt = 7
    Gte = 8
    Lt = 9
    Lte = 10


class BinaryOperationNode(Node):
    def __init__(self, op: Operator, left: ExpressionNode, right: ExpressionNode):
        super().__init__()
        self.op = op
        self.left = left
        self.right = right

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_binary(self)


class FunctionNode(Node):
    def __init__(self, target: str, arguments: List[ExpressionNode]):
        super().__init__()
        self.target = target
        self.arguments = arguments

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_function(self)
