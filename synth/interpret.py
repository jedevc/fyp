from typing import Iterable, List

from .block import (
    Block,
    Call,
    ExpressionStatement,
    Function,
    FunctionDefinition,
    If,
    Statement,
)
from .chunk import ChunkSet, Variable


class Program:
    def __init__(self):
        self.globals = []
        self.functions = []

    def add_global(self, var: Variable):
        self.globals.append(var)

    def add_function(self, func: FunctionDefinition):
        self.functions.append(func)

    @property
    def code(self) -> str:
        parts = []
        parts += [f"{var.code};" for var in self.globals]
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

        return final

    def _transform(self, stmts: Iterable[Statement]) -> Iterable[Statement]:
        for stmt in stmts:
            if isinstance(stmt, Call):
                new_stmt = ExpressionStatement(Function(stmt.block.name, []))
                yield new_stmt
            elif isinstance(stmt, If):
                yield If(stmt.condition, list(self._transform(stmt.statements)))
            else:
                yield stmt
