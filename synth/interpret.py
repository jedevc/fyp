import random
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
        self.blocks = {block.name: block for block in blocks}
        self.chunks = chunks

        self.func_blocks = {block.name for block in blocks if random.random() > 0.5}
        self.inline_blocks = {
            block.name for block in blocks if block.name not in self.func_blocks
        }

    def program(self) -> Program:
        final = Program()

        for blname, block in self.blocks.items():
            if blname != "main" and blname not in self.func_blocks:
                continue

            func = FunctionDefinition(blname, [])
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
                if stmt.block.name in self.func_blocks:
                    new_stmt = ExpressionStatement(Function(stmt.block.name, []))
                    yield new_stmt
                elif stmt.block.name in self.inline_blocks:
                    for st in self._transform(self.blocks[stmt.block.name].statements):
                        yield st
                else:
                    raise RuntimeError()
            elif isinstance(stmt, If):
                yield If(
                    [
                        (condition, list(self._transform(stmts)))
                        for condition, stmts in stmt.groups
                    ]
                )
            else:
                yield stmt
