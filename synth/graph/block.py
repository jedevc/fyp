from typing import Any, Callable, List, Optional, Sequence, Tuple, Union

from ..node import Operator as OperatorType
from ..node import TypeNode
from .chunk import Chunk, ChunkVariable, merge_chunks

Lvalue = Union["Variable", "Array", "Deref"]
Expression = Union["Operation", "Function", "Value", "Ref", "Cast", Lvalue]
Statement = Union["Assignment", "Call", "If", "While", "ExpressionStatement"]


class ExpressionStatement:
    def __init__(self, expr: Expression):
        self.expr = expr

    def traverse(self, func: Callable[[Any], None]):
        func(self)
        self.expr.traverse(func)


class Block:
    def __init__(self, name: str):
        self.name = name
        self.statements: List[Statement] = []

    def traverse(self, func: Callable[[Any], None]):
        func(self)
        for stmt in self.statements:
            stmt.traverse(func)

    def add_statement(self, statement: Statement):
        self.statements.append(statement)

    def add_statements(self, statements: List[Statement]):
        self.statements.extend(statements)

    def __repr__(self) -> str:
        return f"<Block {self.name}>"


class FunctionDefinition:
    def __init__(self, func: str, args: List[ChunkVariable]):
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

    def traverse(self, func: Callable[[Any], None]):
        func(self)
        self.target.traverse(func)
        self.value.traverse(func)


class Deref:
    def __init__(self, target: Lvalue):
        self.target = target

    def traverse(self, func: Callable[[Any], None]):
        func(self)
        self.target.traverse(func)

    def __repr__(self) -> str:
        return f"<Deref {self.target}>"


class Ref:
    def __init__(self, target: Lvalue):
        self.target = target

    def traverse(self, func: Callable[[Any], None]):
        func(self)
        self.target.traverse(func)

    def __repr__(self) -> str:
        return f"<Ref {self.target}>"


class Array:
    def __init__(self, target: Lvalue, index: Expression):
        self.target = target
        self.index = index

    def traverse(self, func: Callable[[Any], None]):
        func(self)
        self.target.traverse(func)
        self.index.traverse(func)

    def __repr__(self) -> str:
        return f"<Array {self.index} {self.target}>"


class Call:
    def __init__(self, block: Block):
        self.block = block

    def traverse(self, func: Callable[[Any], None]):
        func(self)

        # NOTE: do *not* traverse here, as infinite loops can occur, instead it
        # should be up to the caller to handle appropriately

    def __repr__(self) -> str:
        return f"<Call to {self.block.name}>"


class If:
    def __init__(
        self,
        groups: List[Tuple[Optional[Expression], List[Statement]]],
    ):
        self.groups = groups

    def traverse(self, func: Callable[[Any], None]):
        func(self)
        for expr, stmts in self.groups:
            if expr is not None:
                expr.traverse(func)
            for stmt in stmts:
                stmt.traverse(func)


class While:
    def __init__(self, condition: Expression, stmts: List[Statement]):
        self.condition = condition
        self.statements = stmts

    def traverse(self, func: Callable[[Any], None]):
        func(self)
        self.condition.traverse(func)
        for stmt in self.statements:
            stmt.traverse(func)


class Variable:
    def __init__(self, variable: ChunkVariable):
        self.variable = variable

    def traverse(self, func: Callable[[Any], None]):
        func(self)

    def __repr__(self) -> str:
        return f"<Variable {self.variable}>"


class Function:
    def __init__(self, func: Variable, args: Sequence[Expression]):
        self.func = func
        self.args = args

    def traverse(self, func: Callable[[Any], None]):
        func(self)
        for arg in self.args:
            arg.traverse(func)


class Operation:
    def __init__(self, op: OperatorType, left: Expression, right: Expression):
        self.op = op
        self.left = left
        self.right = right

    def traverse(self, func: Callable[[Any], None]):
        func(self)
        self.left.traverse(func)
        self.right.traverse(func)


class Value:
    def __init__(self, value: str):
        self.value = value

    def traverse(self, func: Callable[[Any], None]):
        func(self)

    def __repr__(self) -> str:
        return f"<Value {self.value}>"


class Cast:
    def __init__(self, expr: Expression, tp: TypeNode):
        self.expr = expr
        self.cast = tp

    def traverse(self, func: Callable[[Any], None]):
        func(self)
        self.expr.traverse(func)
