import random
from typing import Callable, Dict, Iterable, List, Optional, Set

from .graph import (
    Block,
    Call,
    Chunk,
    ChunkVariable,
    ExpressionStatement,
    Function,
    FunctionDefinition,
    If,
    Program,
    Statement,
    Variable,
    While,
)
from .utils import find_common_prefix


class Interpreter:
    """
    Utility for translating an abstract representation of code into concrete
    language features.

    To do this, we assign (randomly, but guided through heuristics), an
    interpreation to each abstract item, and then instantiate it.
    """

    def __init__(self, blocks: List[Block], chunks: List[Chunk], extern: Chunk):
        self.blocks = {block.name: block for block in blocks}

        self.chunks = chunks
        self.extern = extern

        # assign each block an interpretation
        self.func_blocks = {block for block in blocks if random.random() > 0}
        self.inline_blocks = {
            block for block in blocks if block not in self.func_blocks
        }

        # assign each chunk an interpretation
        self.local_chunks = {
            chunk for chunk in chunks if chunk.constraint.eof or random.random() > 0.5
        }
        self.global_chunks = {
            chunk for chunk in chunks if chunk not in self.local_chunks
        }

        traces = Tracer(self.blocks["main"])

        # determine functions that local chunks should be allocated on
        self.block_locals: Dict[Block, List[Chunk]] = {}
        for chunk in self.local_chunks:
            root = traces.root(chunk, lambda bl: bl in self.func_blocks)
            if root is None:
                root = self.blocks["main"]

            if root not in self.block_locals:
                self.block_locals[root] = []
            self.block_locals[root].append(chunk)

        # determine patches to make for function blocks
        self.block_patches = {}
        for block, patches in traces.patches.items():
            if block not in self.func_blocks:
                continue

            self.block_patches[block] = [
                patch for patch in patches if patch.chunk in self.local_chunks
            ]

    def program(self) -> Program:
        final = Program()

        for blname, block in self.blocks.items():
            if blname != "main" and block not in self.func_blocks:
                continue

            if block in self.block_patches:
                func = FunctionDefinition(blname, self.block_patches[block])
            else:
                func = FunctionDefinition(blname, [])

            for stmt in self._transform(block.statements):
                func.add_statement(stmt)
            if block in self.block_locals:
                for chunk in self.block_locals[block]:
                    func.add_locals(chunk)

            final.add_function(func)

        for chunk in self.chunks:
            if chunk in self.global_chunks:
                for var in chunk.variables:
                    final.add_global(var)
        for var in self.extern.variables:
            final.add_extern(var)

        return final

    def _transform(self, stmts: Iterable[Statement]) -> Iterable[Statement]:
        for stmt in stmts:
            if isinstance(stmt, Call):
                if stmt.block in self.func_blocks:
                    if stmt.block in self.block_patches:
                        args = [Variable(var) for var in self.block_patches[stmt.block]]
                    else:
                        args = []

                    cvar = ChunkVariable(stmt.block.name, None, None)
                    new_stmt = ExpressionStatement(Function(Variable(cvar), args))
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


class Tracer:
    """
    Tracer to traverse the Block graph, finding references to chunks and
    variables, and their respective paths.

    Essentially, we perform these computations to establish primitives that can
    be used in creating more complex heuristics, and properly interpreting
    blocks and chunks.
    """

    def __init__(self, base: Block):
        self.base = base

        self.paths: Dict[Chunk, List[List[Call]]] = {}
        self.variables: Dict[Block, Set[ChunkVariable]] = {}
        self._trace(base, [])

        self.prefixes = {
            chunk: find_common_prefix(path) for chunk, path in self.paths.items()
        }

        self.patches: Dict[Block, List[ChunkVariable]] = {}

        for chunk, paths in self.paths.items():
            prefix = self.prefixes[chunk]
            for path in paths:
                collected = set()
                for call in reversed(path[len(prefix) :]):
                    bl = call.block
                    collected |= self.variables[bl]
                    if bl in self.patches:
                        self.patches[bl] = list(set(self.patches[bl]) | collected)
                    else:
                        self.patches[bl] = list(collected)

    def root(
        self, chunk: Chunk, predicate: Optional[Callable[[Block], bool]] = None
    ) -> Optional[Block]:
        """
        Find the deepest block node that contains all references to a chunk,
        such that no siblings of the result reference the chunk.
        """

        if chunk not in self.prefixes:
            return None

        prefix = self.prefixes[chunk]

        if predicate:
            while len(prefix) > 0 and not predicate(prefix[-1].block):
                prefix.pop()

        if len(prefix) == 0:
            return self.base
        else:
            return prefix[-1].block

    def _trace(self, base: Block, prefix: List[Call]):
        chunks = set()
        variables = set()

        def finder(part):
            nonlocal chunks

            if isinstance(part, Variable):
                chunks.add(part.variable.chunk)
                variables.add(part.variable)
            elif isinstance(part, Function):
                chunks.add(part.func.variable.chunk)
                variables.add(part.func.variable)
            elif isinstance(part, Call):
                self._trace(part.block, prefix + [part])

        base.traverse(finder)

        for chunk in chunks:
            if chunk not in self.paths:
                self.paths[chunk] = []

            self.paths[chunk].append(prefix)

        self.variables[base] = variables
