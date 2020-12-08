from typing import List, Union

from .base import Node, X
from .expr import Expression, Lvalue
from .visitor import Visitor

Statement = Union[
    "AssignmentNode",
    "CallNode",
    "SplitNode",
    "IfNode",
    "WhileNode",
    "ExpressionStatementNode",
]


class CallNode(Node):
    def __init__(self, target: str):
        super().__init__()
        self.target = target

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_call(self)


class SplitNode(Node):
    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_split(self)


class AssignmentNode(Node):
    def __init__(self, target: Lvalue, expression: Expression):
        super().__init__()
        self.target = target
        self.expression = expression

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_assignment(self)


class IfNode(Node):
    def __init__(
        self,
        condition: Expression,
        if_statements: List[Statement],
        else_statements: List[Statement],
    ):
        super().__init__()
        self.condition = condition
        self.if_statements = if_statements
        self.else_statements = else_statements

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_if(self)


class WhileNode(Node):
    def __init__(
        self,
        condition: Expression,
        statements: List[Statement],
    ):
        super().__init__()
        self.condition = condition
        self.statements = statements

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_while(self)


class ExpressionStatementNode(Node):
    def __init__(self, expression: Expression):
        super().__init__()
        self.expression = expression

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_exprstmt(self)
