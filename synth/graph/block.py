from typing import List, Optional, Tuple, Union

from ..node import Operator as OperatorType
from .chunk import Chunk, ChunkVariable, merge_chunks

Lvalue = Union["Variable", "Array", "Deref"]
Expression = Union["Operation", "Function", "Value", "Ref", Lvalue]
Statement = Union["Assignment", "Call", "If", "While", "ExpressionStatement"]


class ExpressionStatement:
    def __init__(self, expr: Expression):
        self.expr = expr


class Block:
    def __init__(self, name: str):
        self.name = name
        self.statements: List[Statement] = []

    def add_statement(self, statement: Statement):
        self.statements.append(statement)


class FunctionDefinition:
    def __init__(self, func: str, args: List[str]):
        self.func = func
        self.args = args

        self.locals: Optional[Chunk] = None
        self.statements: List[Statement] = []

    def add_local(self, var: ChunkVariable):
        if self.locals:
            self.locals.add_variable(var)
        else:
            self.locals = Chunk([var])

    def add_locals(self, chunk: Chunk):
        self.locals = merge_chunks(self.locals, chunk)

    def add_statement(self, statement: Statement):
        self.statements.append(statement)


class Assignment:
    def __init__(self, target: Lvalue, value: Expression):
        self.target = target
        self.value = value


class Deref:
    def __init__(self, target: Lvalue):
        self.target = target


class Ref:
    def __init__(self, target: Lvalue):
        self.target = target


class Array:
    def __init__(self, target: Lvalue, index: Expression):
        self.target = target
        self.index = index


class Call:
    def __init__(self, block: Block):
        self.block = block


class If:
    def __init__(
        self,
        groups: List[Tuple[Optional[Expression], List[Statement]]],
    ):
        self.groups = groups


class While:
    def __init__(self, condition: Expression, stmts: List[Statement]):
        self.condition = condition
        self.statements = stmts


class Function:
    def __init__(self, func: str, args: List[Expression]):
        self.func = func
        self.args = args


class Operation:
    def __init__(self, op: OperatorType, left: Expression, right: Expression):
        self.op = op
        self.left = left
        self.right = right


class Variable:
    def __init__(self, variable: str, chunk: Optional[Chunk]):
        self.variable = variable
        self.chunk = chunk


class Value:
    def __init__(self, value: str):
        self.value = value
