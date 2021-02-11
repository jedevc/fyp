from typing import Callable, List, Optional, Sequence, Tuple, TypeVar, Union

from ..node import Operator as OperatorType
from ..node import TypeNode
from .chunk import Chunk, ChunkVariable, merge_chunks

Lvalue = Union["Variable", "Array", "Deref"]
Expression = Union["Operation", "Function", "Value", "Ref", "Cast", Lvalue]
Statement = Union["Assignment", "Call", "If", "While", "ExpressionStatement"]

_counter = 0

B = TypeVar("B", bound="BlockItem")

TraversalFunc = Callable[["BlockItem"], None]
MappingFunc = Callable[[B], B]


class BlockItem:
    def __init__(self, known_id: Optional[int] = None):
        if known_id is None:
            global _counter  # pylint: disable=global-statement
            self.id = _counter
            _counter += 1
        else:
            self.id = known_id

    def traverse(self, func: TraversalFunc):
        pass

    def map(self, func: MappingFunc) -> "BlockItem":
        return func(self)


class ExpressionStatement(BlockItem):
    def __init__(self, expr: Expression, known_id: Optional[int] = None):
        super().__init__(known_id)
        self.expr = expr

    def traverse(self, func: TraversalFunc) -> None:
        func(self)
        self.expr.traverse(func)

    def map(self, func: MappingFunc) -> "ExpressionStatement":
        return func(ExpressionStatement(self.expr.map(func), self.id))


class Block(BlockItem):
    def __init__(
        self,
        name: str,
        stmts: Optional[List[Statement]] = None,
        known_id: Optional[int] = None,
    ):
        super().__init__(known_id)
        self.name = name
        self.statements: List[Statement] = stmts or []

    def traverse(self, func: TraversalFunc) -> None:
        func(self)
        for stmt in self.statements:
            stmt.traverse(func)

    def map(self, func: MappingFunc) -> "Block":
        return func(
            Block(self.name, [stmt.map(func) for stmt in self.statements], self.id)
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
        func(self)

        # NOTE: do *not* traverse here, as infinite loops can occur, instead it
        # should be up to the caller to handle appropriately

    def map(self, func: MappingFunc) -> "Call":
        return self

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


class Variable(BlockItem):
    def __init__(self, variable: ChunkVariable, known_id: Optional[int] = None):
        super().__init__(known_id)
        self.variable = variable

    def traverse(self, func: TraversalFunc) -> None:
        func(self)

    def map(self, func: MappingFunc) -> "Variable":
        return func(self)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.variable}>"


class Function(BlockItem):
    def __init__(
        self, func: Variable, args: Sequence[Expression], known_id: Optional[int] = None
    ):
        super().__init__(known_id)
        self.func = func
        self.args = args

    def traverse(self, func: TraversalFunc) -> None:
        func(self)
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
        left: Expression,
        right: Expression,
        known_id: Optional[int] = None,
    ):
        super().__init__(known_id)
        self.op = op
        self.left = left
        self.right = right

    def traverse(self, func: TraversalFunc) -> None:
        func(self)
        self.left.traverse(func)
        self.right.traverse(func)

    def map(self, func: MappingFunc) -> "Operation":
        return func(
            Operation(self.op, self.left.map(func), self.right.map(func), self.id)
        )


class Value(BlockItem):
    def __init__(self, value: str, known_id: Optional[int] = None):
        super().__init__(known_id)
        self.value = value

    def traverse(self, func: TraversalFunc) -> None:
        func(self)

    def map(self, func: MappingFunc) -> "Value":
        return func(self)

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
