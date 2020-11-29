from typing import Any, List, Union

from .base import Node
from .expr import Expression, Lvalue
from .visitor import Visitor

Statement = Union["AssignmentNode", "CallNode", "IfNode", "ExpressionStatementNode"]


class CallNode(Node):
    def __init__(self, target: str):
        super().__init__()
        self.target = target

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_call(self)


class AssignmentNode(Node):
    def __init__(self, target: Lvalue, expression: Expression):
        super().__init__()
        self.target = target
        self.expression = expression

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_assignment(self)


class IfNode(Node):
    def __init__(self, condition: Expression, statements: List[Statement]):
        super().__init__()
        self.condition = condition
        self.statements = statements

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_if(self)


class ExpressionStatementNode(Node):
    def __init__(self, expression: Expression):
        super().__init__()
        self.expression = expression

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_exprstmt(self)
