from typing import Iterable, List

from .graph import (
    Block,
    Call,
    ChunkSet,
    ExpressionStatement,
    Function,
    FunctionDefinition,
    If,
    Program,
    Statement,
)


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
