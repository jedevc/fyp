import random
from typing import Dict, List, Set

from ..assets import Asset
from ..graph import (
    Block,
    BlockItem,
    Call,
    Chunk,
    ChunkVariable,
    Expression,
    ExpressionStatement,
    Function,
    FunctionDefinition,
    Program,
    StatementGroup,
    Variable,
)
from .lifter import Lifter, UsageCapture
from .trace import Tracer
from .utils import repair_calls


class Interpreter:
    """
    Utility for translating an abstract representation of code into concrete
    language features.

    To do this, we assign (randomly, but guided through heuristics), an
    interpreation to each abstract item, and then instantiate it.
    """

    def __init__(self, asset: Asset):
        self.blocks: Dict[str, Block] = {block.name: block for block in asset.blocks}

        self.chunks: List[Chunk] = asset.chunks
        self.extern: Chunk = asset.extern

        self.func_blocks: Set[str] = set()
        self.inline_blocks: Set[str] = set()
        self.local_chunks: Set[Chunk] = set()
        self.global_chunks: Set[Chunk] = set()

        self.block_locals: Dict[str, List[Chunk]] = {}
        self.function_signature: Dict[str, List[ChunkVariable]] = {}

        self.substitutions: Dict[int, Expression] = {}
        self.maximals: Dict[str, Dict[str, UsageCapture]] = {}

        self._randomize()

        for blname, block in self.blocks.items():
            block = self._apply_inline_calls(block)
            self.blocks[blname] = block

        self.blocks = {
            block.name: block for block in repair_calls(list(self.blocks.values()))
        }

        self._trace()

        for blname in self.func_blocks:
            # the inline blocks have already been handled

            block = self.blocks[blname]
            block = self._apply_lifts(block)
            block = self._apply_calls(block)
            self.blocks[blname] = block

    def program(self) -> Program:
        program = Program()

        # create functions
        for blname, block in self.blocks.items():
            if blname not in self.func_blocks:
                continue

            if blname in self.function_signature:
                func = FunctionDefinition(blname, self.function_signature[blname])
            else:
                func = FunctionDefinition(blname, [])

            for stmt in block.statements:
                func.add_statement(stmt)
            if blname in self.block_locals:
                for chunk in self.block_locals[blname]:
                    func.add_locals(chunk, static=chunk.constraint.static)

            program.add_function(func)

        # create global variables
        for chunk in self.chunks:
            if chunk in self.global_chunks:
                for var in chunk.variables:
                    program.add_global(var)
        # create extern variables
        for var in self.extern.variables:
            program.add_extern(var)

        return program

    def _randomize(self):
        # assign each block an interpretation
        self.func_blocks: Set[str] = set()
        self.inline_blocks: Set[str] = set()
        for blname, block in self.blocks.items():
            if blname == "main" or block.constraint.func:
                self.func_blocks.add(blname)
            elif block.constraint.inline:
                self.inline_blocks.add(blname)
            else:
                if random.random() > 0.5:
                    self.func_blocks.add(blname)
                else:
                    self.inline_blocks.add(blname)

        # assign each chunk an interpretation
        self.local_chunks: Set[Chunk] = set()
        self.global_chunks: Set[Chunk] = set()
        for chunk in self.chunks:
            if chunk.constraint.islocal:
                self.local_chunks.add(chunk)
            elif chunk.constraint.isglobal:
                self.global_chunks.add(chunk)
            else:
                if random.random() > 0.5:
                    self.local_chunks.add(chunk)
                else:
                    self.global_chunks.add(chunk)

    def _trace(self):
        assert "main" in self.blocks
        traces = Tracer(self.blocks["main"])

        # determine functions that local chunks should be allocated on
        for chunk in self.local_chunks:
            root = traces.root(chunk)
            if root is None:
                root = self.blocks["main"]

            if root.name in self.block_locals:
                self.block_locals[root.name].append(chunk)
            else:
                self.block_locals[root.name] = [chunk]

        # determine signatures of functions
        for block, patches in traces.patches.items():
            if block.name in self.func_blocks:
                patches = [
                    patch for patch in patches if patch.chunk in self.local_chunks
                ]
            else:
                patches = []

            self.function_signature[block.name] = patches

        # patch function signatures
        for func, args in self.function_signature.items():
            self.maximals[func] = {}
            for i, arg in enumerate(args):
                maximal, narg, subs = Lifter.lift(self.blocks[func], arg)

                self.function_signature[func][i] = narg
                self.maximals[func][arg.name] = maximal
                self.substitutions = {**self.substitutions, **subs}

    def _apply_lifts(self, block: Block) -> Block:
        def mapper(item: BlockItem) -> BlockItem:
            if item.id in self.substitutions:
                return self.substitutions[item.id]
            else:
                return item

        return block.map(mapper)

    def _apply_inline_calls(self, block: Block) -> Block:
        def mapper(item: BlockItem) -> BlockItem:
            item.id = BlockItem.new_id()
            if not isinstance(item, Call):
                return item

            if item.block.name in self.inline_blocks:
                group = [
                    stmt.map(mapper) for stmt in self.blocks[item.block.name].statements
                ]
                return StatementGroup(group)
            elif item.block.name in self.func_blocks:
                return item
            else:
                print(item.block)
                print(self.blocks)
                raise RuntimeError()

        return block.map(mapper)

    def _apply_calls(self, block: Block) -> Block:
        def mapper(item: BlockItem) -> BlockItem:
            if not isinstance(item, Call):
                return item

            if item.block.name in self.func_blocks:
                if item.block.name in self.function_signature:
                    args = []
                    for arg in self.function_signature[item.block.name]:
                        target = self.maximals[item.block.name][arg.name]
                        try:
                            current = self.maximals[block.name][arg.name]
                        except KeyError:
                            for chunk in self.chunks:
                                if (var := chunk.lookup(arg.name)) :
                                    current = UsageCapture(var, Variable(var))
                                    break

                        narg = Lifter.rewrite(target, current)
                        args.append(narg.capture)
                else:
                    args = []

                cvar = ChunkVariable(item.block.name, None, None)
                new_stmt = ExpressionStatement(Function(Variable(cvar), args))
                return new_stmt
            elif item.block.name in self.inline_blocks:
                raise RuntimeError()
            else:
                raise RuntimeError()

        return block.map(mapper)
