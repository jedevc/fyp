import random
from typing import Iterable, List

from .graph import (
    Block,
    Call,
    Chunk,
    ExpressionStatement,
    Function,
    FunctionDefinition,
    If,
    Program,
    Statement,
    Variable,
    While,
)


class Interpreter:
    def __init__(self, blocks: List[Block], chunks: List[Chunk], extern: Chunk):
        self.blocks = {block.name: block for block in blocks}

        self.func_blocks = {block for block in blocks if random.random() > 0.5}
        self.inline_blocks = {
            block for block in blocks if block not in self.func_blocks
        }

        self.chunks = chunks
        self.extern = extern

        self.global_chunks = {chunk for chunk in chunks if random.random() > 0.5}
        self.stack_chunks = {
            chunk for chunk in chunks if chunk not in self.global_chunks
        }

    def program(self) -> Program:
        final = Program()

        for blname, block in self.blocks.items():
            if blname != "main" and block not in self.func_blocks:
                continue

            func = FunctionDefinition(blname, [])
            for stmt in self._transform(block.statements):
                func.add_statement(stmt)
            # TODO: can add function arguments here
            final.add_function(func)

        for chunk in self.chunks:
            if chunk in self.global_chunks:
                for var in chunk.variables:
                    final.add_global(var)
        for var in self.extern.variables:
            final.add_extern(var)

        return final

    def _find_chunk_refs(
        self, chunk: Chunk, base: Block, prefix: List[Call]
    ) -> List[List[Call]]:
        matches = False
        paths = []

        def finder(part):
            nonlocal matches, paths

            if isinstance(part, Variable):
                if part.chunk == chunk:
                    matches = True
            elif isinstance(part, Call):
                newpaths = self._find_chunk_refs(chunk, part.block, prefix + [part])
                paths.extend(newpaths)

        base.traverse(finder)

        if matches:
            paths.append(prefix)
        return paths

    def _transform(self, stmts: Iterable[Statement]) -> Iterable[Statement]:
        for stmt in stmts:
            if isinstance(stmt, Call):
                if stmt.block in self.func_blocks:
                    new_stmt = ExpressionStatement(Function(stmt.block.name, []))
                    yield new_stmt
                elif stmt.block in self.inline_blocks:
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
            elif isinstance(stmt, While):
                yield While(stmt.condition, list(self._transform(stmt.statements)))
            else:
                yield stmt
