import random
from typing import Any, Dict, Iterable, List

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

        self.global_chunks = {chunk for chunk in chunks if random.random() > 1}
        self.local_chunks = {
            chunk for chunk in chunks if chunk not in self.global_chunks
        }

        self.blocks_with_locals: Dict[Block, List[Chunk]] = {}
        for chunk in self.local_chunks:
            result = self._find_chunk_refs(chunk, self.blocks["main"], [])

            prefix = find_common_prefix(result)
            while len(prefix) > 0 and prefix[-1].block not in self.func_blocks:
                prefix.pop()

            if len(prefix) == 0:
                bl = self.blocks["main"]
            else:
                bl = prefix[-1].block

            if bl in self.blocks_with_locals:
                self.blocks_with_locals[bl].append(chunk)
            else:
                self.blocks_with_locals[bl] = [chunk]

    def program(self) -> Program:
        final = Program()

        for blname, block in self.blocks.items():
            if blname != "main" and block not in self.func_blocks:
                continue

            func = FunctionDefinition(blname, [])
            for stmt in self._transform(block.statements):
                func.add_statement(stmt)
            if block in self.blocks_with_locals:
                for chunk in self.blocks_with_locals[block]:
                    func.add_locals(chunk)

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
                    yield from self._transform(self.blocks[stmt.block.name].statements)
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


def find_common_prefix(lists: List[List[Any]]) -> List[Any]:
    if len(lists) == 0:
        return []

    prefix = lists[0]
    for li in lists[1:]:
        mismatch = False
        count = min(len(li), len(prefix))
        for i in range(count):
            if prefix[i] != li[i]:
                mismatch = True
                break

        if mismatch:
            prefix = prefix[:i]
        else:
            prefix = prefix[:count]

    return prefix
