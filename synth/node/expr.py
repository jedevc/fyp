from enum import Enum, unique
from typing import List, Optional, Union

from .base import Node, X
from .types import TypeNode
from .visitor import Visitor

LvalueNode = Union["VariableNode", "ArrayNode", "DerefNode", "LiteralNode"]
ExpressionNode = Union[
    "BinaryOperationNode",
    "CastNode",
    "FunctionNode",
    "ValueNode",
    "RefNode",
    LvalueNode,
]


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

    And = 11
    Or = 12


BOOLEAN_OPERATORS = (Operator.And, Operator.Or)
COMPARISON_OPERATORS = (
    Operator.Eq,
    Operator.Neq,
    Operator.Gt,
    Operator.Gte,
    Operator.Lt,
    Operator.Lte,
)
ARITHMETIC_OPERATORS = (
    Operator.Add,
    Operator.Subtract,
    Operator.Multiply,
    Operator.Divide,
)


class ValueNode(Node):
    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_value(self)


class IntValueNode(ValueNode):
    def __init__(self, value: int, base: int):
        super().__init__()
        self.value = value
        self.base = base


class FloatValueNode(ValueNode):
    def __init__(self, left: int, right: int):
        super().__init__()
        self.left = left
        self.right = right


class BoolValueNode(ValueNode):
    def __init__(self, value: bool):
        super().__init__()
        self.value = value


class StringValueNode(ValueNode):
    def __init__(self, value: str):
        super().__init__()
        self.value = value


class TemplateValueNode(ValueNode):
    def __init__(self, name: str, definition: Optional[str]):
        super().__init__()
        self.name = name
        self.definition = definition

    def construct(self, source: Union[str, bool, int, float]) -> ValueNode:
        node: ValueNode
        if isinstance(source, str):
            node = StringValueNode(source)
        elif isinstance(source, bool):
            node = BoolValueNode(source)
        elif isinstance(source, int):
            node = IntValueNode(source, 10)
        elif isinstance(source, float):
            lhs, rhs = f"{source:.20f}".split(".")
            node = FloatValueNode(int(lhs), int(rhs))
        else:
            raise TypeError(f"cannot construct value from {type(source)}")

        node.token_start = self.token_start
        node.token_end = self.token_end

        return node


class LiteralNode(Node):
    def __init__(self, content: str):
        super().__init__()
        self.content = content

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_literal(self)


class CastNode(Node):
    def __init__(self, expr: ExpressionNode, tp: TypeNode):
        super().__init__()
        self.expr = expr
        self.cast = tp

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_cast(self)


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


class BinaryOperationNode(Node):
    def __init__(self, op: Operator, left: ExpressionNode, right: ExpressionNode):
        super().__init__()
        self.op = op
        self.left = left
        self.right = right

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_binary(self)


class FunctionNode(Node):
    def __init__(self, target: ExpressionNode, arguments: List[ExpressionNode]):
        super().__init__()
        self.target = target
        self.arguments = arguments

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_function(self)
