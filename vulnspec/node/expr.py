from enum import Enum, unique
from typing import TYPE_CHECKING, List, Union

from .base import Node, X
from .types import TypeNode
from .visitor import Visitor

if TYPE_CHECKING:
    from .value import ValueNode

LvalueNode = Union["VariableNode", "ArrayNode", "DerefNode", "LiteralExpressionNode"]
ExpressionNode = Union[
    "UnaryOperationNode",
    "BinaryOperationNode",
    "CastNode",
    "FunctionNode",
    "ValueNode",
    "RefNode",
    "SizeOfExprNode",
    "SizeOfTypeNode",
    LvalueNode,
]


@unique
class Operator(Enum):
    Add = 1
    Subtract = 2
    Multiply = 3
    Divide = 4
    Negate = 5

    Eq = 6
    Neq = 7
    Gt = 8
    Gte = 9
    Lt = 10
    Lte = 11

    Not = 12
    And = 13
    Or = 14

    BitwiseNot = 15
    BitwiseAnd = 16
    BitwiseOr = 17
    BitwiseXor = 18

    def opstr(self) -> str:
        return {
            Operator.Add: "+",
            Operator.Subtract: "-",
            Operator.Multiply: "*",
            Operator.Divide: "/",
            Operator.Negate: "-",
            Operator.Eq: "==",
            Operator.Neq: "!=",
            Operator.Gt: ">",
            Operator.Gte: ">=",
            Operator.Lt: "<",
            Operator.Lte: "<=",
            Operator.Not: "!",
            Operator.And: "&&",
            Operator.Or: "||",
            Operator.BitwiseNot: "~",
            Operator.BitwiseAnd: "&",
            Operator.BitwiseOr: "|",
            Operator.BitwiseXor: "^",
        }[self]


BOOLEAN_OPERATORS = (Operator.And, Operator.Or, Operator.Not)
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
    Operator.Negate,
)
BITWISE_OPERATORS = (
    Operator.BitwiseAnd,
    Operator.BitwiseOr,
    Operator.BitwiseXor,
    Operator.BitwiseNot,
)


class SizeOfExprNode(Node):
    def __init__(self, target: ExpressionNode):
        super().__init__()
        self.target = target

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_sizeof_expr(self)


class SizeOfTypeNode(Node):
    def __init__(self, target: TypeNode):
        super().__init__()
        self.target = target

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_sizeof_type(self)


class LiteralExpressionNode(Node):
    def __init__(self, content: str):
        super().__init__()
        self.content = content

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_literal_expr(self)


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


class UnaryOperationNode(Node):
    def __init__(self, op: Operator, item: ExpressionNode):
        super().__init__()
        self.op = op
        self.item = item

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_unary(self)


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
