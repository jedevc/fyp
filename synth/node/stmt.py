from typing import List, Optional, Union

from .base import Node, X
from .expr import ExpressionNode, LvalueNode
from .visitor import Visitor

StatementNode = Union[
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
    def __init__(self, target: LvalueNode, expression: ExpressionNode):
        super().__init__()
        self.target = target
        self.expression = expression

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_assignment(self)


class IfNode(Node):
    def __init__(
        self,
        condition: ExpressionNode,
        statements: List[StatementNode],
        else_action: Optional[Union["IfNode", List[StatementNode]]],
    ):
        super().__init__()
        self.condition = condition
        self.statements = statements

        self.else_if = None
        self.else_statements = None
        if else_action is None:
            pass
        elif isinstance(else_action, IfNode):
            self.else_if = else_action
        else:
            self.else_statements = else_action

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_if(self)


class WhileNode(Node):
    def __init__(
        self,
        condition: ExpressionNode,
        statements: List[StatementNode],
    ):
        super().__init__()
        self.condition = condition
        self.statements = statements

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_while(self)


class ExpressionStatementNode(Node):
    def __init__(self, expression: ExpressionNode):
        super().__init__()
        self.expression = expression

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_exprstmt(self)
