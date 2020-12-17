from typing import Iterable, List

from .graph import (
    Block,
    Call,
    ChunkSet,
    ChunkVariable,
    ExpressionStatement,
    Function,
    FunctionDefinition,
    If,
    Statement,
)


class Program:
    def __init__(self):
        self.globals = []
        self.externs = []

        self.functions = []

    def add_global(self, var: ChunkVariable):
        self.globals.append(var)

    def add_extern(self, var: ChunkVariable):
        self.externs.append(var)

    def add_function(self, func: FunctionDefinition):
        self.functions.append(func)

    @property
    def code(self) -> str:
        parts = []
        parts += [f"{var.code};" for var in self.globals]
        parts += [f"extern {var.code};" for var in self.externs]
        parts += [func.code for func in self.functions]
        return "\n".join(parts)


class Interpreter:
    def __init__(self, blocks: List[Block], chunks: ChunkSet):
        self.blocks = blocks
        self.chunks = chunks

    def program(self) -> Program:
        final = Program()

        for block in self.blocks:
            func = FunctionDefinition(block.name, [])
            for stmt in self._transform(block.statements):
                func.add_statement(stmt)
            final.add_function(func)

        for var in self.chunks.variables:
            final.add_global(var)
        for var in self.chunks.externs:
            final.add_extern(var)

        return final

    def _transform(self, stmts: Iterable[Statement]) -> Iterable[Statement]:
        for stmt in stmts:
            if isinstance(stmt, Call):
                new_stmt = ExpressionStatement(Function(stmt.block.name, []))
                yield new_stmt
            elif isinstance(stmt, If):
                yield If(
                    stmt.condition,
                    list(self._transform(stmt.ifs)),
                    list(self._transform(stmt.elses)),
                )
            else:
                yield stmt
