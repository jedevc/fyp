from typing import Callable, List, Optional, Sequence, Tuple, TypeVar, Union

from ..error import ConstraintError
from ..node import Operator as OperatorType
from ..node import TypeNode
from .chunk import Chunk, ChunkVariable, merge_chunks

Lvalue = Union["Variable", "Array", "Deref"]
Expression = Union["Operation", "Function", "Value", "Ref", "Cast", Lvalue]
Statement = Union[
    "Assignment", "Call", "If", "While", "ExpressionStatement", "StatementGroup"
]


BI = TypeVar("BI", bound="BlockItem")
TraversalFunc = Callable[[BI], None]
MappingFunc = Callable[[BI], BI]


class BlockItem:
    _counter = 0

    def __init__(self, known_id: Optional[int] = None):
        if known_id is None:
            self.id = BlockItem.new_id()
        else:
            self.id = known_id

    @staticmethod
    def new_id() -> int:
        i = BlockItem._counter
        BlockItem._counter += 1
        return i

    def traverse(self, func: TraversalFunc):
        pass

    def map(self, func: MappingFunc) -> "BlockItem":
        raise NotImplementedError()


class BlockConstraint:
    def __init__(self, func=False, inline=False):
        self.func = func
        self.inline = inline

        self._verify()

    def copy(self) -> "BlockConstraint":
        return BlockConstraint(func=self.func, inline=self.inline)

    def merge(self, other: "BlockConstraint"):
        self.func = self.func or other.func
        self.inline = self.inline or other.inline

        self._verify()

    def _verify(self):
        if self.func and self.inline:
            raise ConstraintError("cannot allow func and inline constraints")

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} func={self.func} inline={self.inline}>"


class Block(BlockItem):
    def __init__(
        self,
        name: str,
        stmts: Optional[List[Statement]] = None,
        constraint: Optional[BlockConstraint] = None,
        known_id: Optional[int] = None,
    ):
        super().__init__(known_id)
        self.name = name
        self.statements: List[Statement] = stmts or []
        self.constraint = BlockConstraint() if constraint is None else constraint

    def traverse(self, func: TraversalFunc) -> None:
        func(self)
        for stmt in self.statements:
            stmt.traverse(func)

    def map(self, func: MappingFunc) -> "Block":
        return func(
            Block(
                self.name,
                [stmt.map(func) for stmt in self.statements],
                self.constraint.copy(),
                self.id,
            )
        )

    def add_statement(self, statement: Statement):
        self.statements.append(statement)

    def add_statements(self, statements: List[Statement]):
        self.statements.extend(statements)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name}>"


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


class Assignment(BlockItem):
    def __init__(
        self, target: Lvalue, value: Expression, known_id: Optional[int] = None
    ):
        super().__init__(known_id)
        self.target = target
        self.value = value

    def traverse(self, func: TraversalFunc) -> None:
        func(self)
        self.target.traverse(func)
        self.value.traverse(func)

    def map(self, func: MappingFunc) -> "Assignment":
        return func(Assignment(self.target.map(func), self.value.map(func), self.id))


class Deref(BlockItem):
    def __init__(self, target: Expression, known_id: Optional[int] = None):
        super().__init__(known_id)
        self.target = target

    def traverse(self, func: TraversalFunc) -> None:
        func(self)
        self.target.traverse(func)

    def map(self, func: MappingFunc) -> "Deref":
        return func(Deref(self.target.map(func), self.id))

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.target}>"


class Ref(BlockItem):
    def __init__(self, target: Lvalue, known_id: Optional[int] = None):
        super().__init__(known_id)
        self.target = target

    def traverse(self, func: TraversalFunc) -> None:
        func(self)
        self.target.traverse(func)

    def map(self, func: MappingFunc) -> "Ref":
        return func(Ref(self.target.map(func), self.id))

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.target}>"


class Array(BlockItem):
    def __init__(
        self, target: Expression, index: Expression, known_id: Optional[int] = None
    ):
        super().__init__(known_id)
        self.target = target
        self.index = index

    def traverse(self, func: TraversalFunc) -> None:
        func(self)
        self.target.traverse(func)
        self.index.traverse(func)

    def map(self, func: MappingFunc) -> "Array":
        return func(Array(self.target.map(func), self.index.map(func), self.id))

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.index} {self.target}>"


class Call(BlockItem):
    def __init__(self, block: Block, known_id: Optional[int] = None):
        super().__init__(known_id)
        self.block = block

    def traverse(self, func: TraversalFunc) -> None:
        # NOTE: do *not* traverse here, as infinite loops can occur, instead it
        # should be up to the caller to handle appropriately

        func(self)

    def map(self, func: MappingFunc) -> "Call":
        # NOTE: same as above!

        return func(Call(self.block, self.id))

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.block.name}>"


class If(BlockItem):
    def __init__(
        self,
        groups: List[Tuple[Optional[Expression], List[Statement]]],
        known_id: Optional[int] = None,
    ):
        super().__init__(known_id)
        self.groups = groups

    def traverse(self, func: TraversalFunc) -> None:
        func(self)
        for expr, stmts in self.groups:
            if expr is not None:
                expr.traverse(func)
            for stmt in stmts:
                stmt.traverse(func)

    def map(self, func: MappingFunc) -> "If":
        ngroups = []
        for expr, stmts in self.groups:
            nexpr = expr.map(func) if expr is not None else None
            nstmts = [stmt.map(func) for stmt in stmts]
            ngroups.append((nexpr, nstmts))
        return If(ngroups, self.id)


class While(BlockItem):
    def __init__(
        self,
        condition: Expression,
        stmts: List[Statement],
        known_id: Optional[int] = None,
    ):
        super().__init__(known_id)
        self.condition = condition
        self.statements = stmts

    def traverse(self, func: TraversalFunc) -> None:
        func(self)
        self.condition.traverse(func)
        for stmt in self.statements:
            stmt.traverse(func)

    def map(self, func: MappingFunc) -> "While":
        return func(
            While(
                self.condition.map(func),
                [stmt.map(func) for stmt in self.statements],
                self.id,
            )
        )


class ExpressionStatement(BlockItem):
    def __init__(self, expr: Expression, known_id: Optional[int] = None):
        super().__init__(known_id)
        self.expr = expr

    def traverse(self, func: TraversalFunc) -> None:
        func(self)
        self.expr.traverse(func)

    def map(self, func: MappingFunc) -> "ExpressionStatement":
        return func(ExpressionStatement(self.expr.map(func), self.id))


class StatementGroup(BlockItem):
    def __init__(self, stmts: List[Statement], known_id: Optional[int] = None):
        super().__init__(known_id)
        self.statements = stmts

    def traverse(self, func: TraversalFunc) -> None:
        func(self)
        for stmt in self.statements:
            stmt.traverse(func)

    def map(self, func: MappingFunc) -> "StatementGroup":
        return func(
            StatementGroup([stmt.map(func) for stmt in self.statements], self.id)
        )


class Variable(BlockItem):
    def __init__(self, variable: ChunkVariable, known_id: Optional[int] = None):
        super().__init__(known_id)
        self.variable = variable

    def traverse(self, func: TraversalFunc) -> None:
        func(self)

    def map(self, func: MappingFunc) -> "Variable":
        return func(Variable(self.variable, self.id))

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.variable}>"


class Function(BlockItem):
    def __init__(
        self,
        func: Expression,
        args: Sequence[Expression],
        known_id: Optional[int] = None,
    ):
        super().__init__(known_id)
        self.func = func
        self.args = args

    def traverse(self, func: TraversalFunc) -> None:
        func(self)
        self.func.traverse(func)
        for arg in self.args:
            arg.traverse(func)

    def map(self, func: MappingFunc) -> "Function":
        return func(
            Function(self.func.map(func), [arg.map(func) for arg in self.args], self.id)
        )


class Operation(BlockItem):
    def __init__(
        self,
        op: OperatorType,
        operands: List[Expression],
        known_id: Optional[int] = None,
    ):
        super().__init__(known_id)
        self.op = op
        self.operands = operands

    def traverse(self, func: TraversalFunc) -> None:
        func(self)
        for operand in self.operands:
            operand.traverse(func)

    def map(self, func: MappingFunc) -> "Operation":
        return func(
            Operation(
                self.op,
                [expr.map(func) for expr in self.operands],
                self.id,
            )
        )


class Value(BlockItem):
    def __init__(self, value: str, known_id: Optional[int] = None):
        super().__init__(known_id)
        self.value = value

    def traverse(self, func: TraversalFunc) -> None:
        func(self)

    def map(self, func: MappingFunc) -> "Value":
        return func(Value(self.value, self.id))

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.value}>"


class Cast(BlockItem):
    def __init__(self, expr: Expression, tp: TypeNode, known_id: Optional[int] = None):
        super().__init__(known_id)
        self.expr = expr
        self.cast = tp

    def traverse(self, func: TraversalFunc) -> None:
        func(self)
        self.expr.traverse(func)

    def map(self, func: MappingFunc) -> "Cast":
        return func(Cast(self.expr.map(func), self.cast, self.id))
