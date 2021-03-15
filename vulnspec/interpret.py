import random
from functools import reduce
from typing import Any, Dict, List, Optional, Set, Tuple

from .graph import (
    Array,
    Assignment,
    Block,
    BlockItem,
    Call,
    Chunk,
    ChunkVariable,
    Deref,
    Expression,
    ExpressionStatement,
    Function,
    FunctionDefinition,
    Program,
    Ref,
    StatementGroup,
    Value,
    Variable,
)
from .node import ArrayTypeNode, PointerTypeNode
from .utils import find_common_prefix


class Interpreter:
    """
    Utility for translating an abstract representation of code into concrete
    language features.

    To do this, we assign (randomly, but guided through heuristics), an
    interpreation to each abstract item, and then instantiate it.
    """

    def __init__(self, blocks: List[Block], chunks: List[Chunk], extern: Chunk):
        self.blocks: Dict[str, Block] = {block.name: block for block in blocks}

        self.chunks: List[Chunk] = chunks
        self.extern: Chunk = extern

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


class Tracer:
    """
    Tracer to traverse the Block graph, finding references to chunks and
    variables, and their respective paths.

    Essentially, we perform these computations to establish primitives that can
    be used in creating more complex heuristics, and properly interpreting
    blocks and chunks.
    """

    def __init__(self, base: Block, recursive: bool = True):
        self.base = base
        self.recursive = recursive

        self.blocks: Set[Block] = set()
        self.paths: Dict[Chunk, List[List[Call]]] = {}
        self.variables: Dict[Block, Set[ChunkVariable]] = {}
        self._trace(base, [])

        self.prefixes = {
            chunk: find_common_prefix(path) for chunk, path in self.paths.items()
        }

        self.patches: Dict[Block, List[ChunkVariable]] = {}
        self.patches[base] = []

        for chunk, paths in self.paths.items():
            prefix = self.prefixes[chunk]
            for path in paths:
                collected = set()
                for call in reversed(path[len(prefix) :]):
                    bl = call.block
                    collected |= {
                        var for var in self.variables[bl] if var.chunk is chunk
                    }
                    if bl in self.patches:
                        self.patches[bl] = list(set(self.patches[bl]) | collected)
                    else:
                        self.patches[bl] = list(collected)

    def root(self, chunk: Chunk) -> Optional[Block]:
        """
        Find the deepest block node that contains all references to a chunk,
        such that no siblings of the result reference the chunk.
        """

        if chunk not in self.prefixes:
            return None

        prefix = self.prefixes[chunk]
        if len(prefix) == 0:
            return self.base
        else:
            return prefix[-1].block

    def _trace(
        self, base: Block, prefix: List[Call], exclude: Optional[Set[Block]] = None
    ):
        exclude = set() if exclude is None else exclude

        chunks: Set[Chunk] = set()
        variables: Set[ChunkVariable] = set()

        def finder(part: BlockItem):
            nonlocal variables

            if isinstance(part, Variable):
                if part.variable.chunk is not None:
                    chunks.add(part.variable.chunk)
                variables.add(part.variable)
            elif isinstance(part, Call):
                assert exclude is not None
                if self.recursive:
                    self._trace(part.block, prefix + [part], exclude | {base})
                    variables |= self.variables[part.block]

        if base not in exclude:
            base.traverse(finder)

        for chunk in chunks:
            if chunk in self.paths:
                self.paths[chunk].append(prefix)
            else:
                self.paths[chunk] = [prefix]

        self.blocks.add(base)
        self.variables[base] = variables


class Lifter:
    """
    Utility methods for lifting variables to their most common usages.

    These functions provide primitives for the interpreter to replace function
    calls, function signatures and variable usages with the lifted paramter.
    """

    class VRef(Ref):
        pass

    @staticmethod
    def capture_usages(
        base: Block,
        var: ChunkVariable,
        recursive: bool = True,
        exclude: Optional[Set[Block]] = None,
    ) -> List["UsageCapture"]:
        """
        Find and capture all the usages (and their contexts) of a variable in a
        block.
        """

        captures: List[UsageCapture] = []
        stack: List[Any] = []

        exclude = set() if exclude is None else exclude

        def finder(part):
            if isinstance(part, Variable) and part.variable == var:
                use = part

                work = list(stack)
                while True:
                    item = work.pop()
                    if isinstance(item, (Ref, Deref, Array)):
                        use = item
                    elif isinstance(item, Assignment):
                        use = Lifter.VRef(use, use.id)
                        break
                    else:
                        break

                captures.append(UsageCapture(var, use))

                stack.append(part)
            else:
                stack.append(part)
                if recursive and isinstance(part, Call):
                    captures.extend(
                        Lifter.capture_usages(part.block, var, True, exclude | {base})
                    )

        if base not in exclude:
            base.traverse(finder)

        return captures

    @staticmethod
    def lift(
        base: Block, var: ChunkVariable
    ) -> Tuple["UsageCapture", ChunkVariable, Dict[int, Expression]]:
        """
        Return all the helpful primitives we can use in constructing the exact
        substitutions to perform to help left parameters.
        """

        captures = Lifter.capture_usages(base, var)
        root = reduce(UsageCapture.maximal, captures)
        root_var = root.nvar()
        root_inv = root.invert()

        translations = {}
        for use in Lifter.capture_usages(base, var, False):
            translations[use.capture.id] = use.replace(root_inv).simplify().capture

        return root, root_var, translations

    @staticmethod
    def rewrite(use: "UsageCapture", ctx: "UsageCapture") -> "UsageCapture":
        """
        Rewrite how a usage would appear in the context of another capture.

        Note that both the usage and the context must both be in the same
        global context.
        """

        use = use.simplify()
        ctx = ctx.simplify()

        ctx_inv = ctx.invert()
        return use.replace(ctx_inv).simplify()


class UsageCapture:
    """
    Representation and utility methods for capturing the context around a
    variable reference. We use these to detect how variables are used, and
    combine them in different ways.
    """

    def __init__(self, var: ChunkVariable, capture: Expression):
        self.var = var
        self.capture = capture

    def nvar(self) -> ChunkVariable:
        return self._nvar(self.capture)

    def invert(self) -> "UsageCapture":
        nvar = self.nvar()
        return UsageCapture(nvar, self._invert(self.capture, Variable(nvar)))

    def simplify(self) -> "UsageCapture":
        return UsageCapture(self.var, self._simplify(self.capture))

    def replace(self, new: "UsageCapture") -> "UsageCapture":
        return UsageCapture(new.var, self._replace(self.capture, new.capture))

    def maximal(self, other: "UsageCapture") -> "UsageCapture":
        return UsageCapture(self.var, self._maximal(self.capture, other.capture))

    def _nvar(self, target: Expression) -> ChunkVariable:
        if isinstance(target, Variable):
            return target.variable
        elif isinstance(target, Ref):
            var = self._nvar(target.target)
            if var.vtype is None:
                return ChunkVariable(var.name, None, var.chunk)
            else:
                return ChunkVariable(var.name, PointerTypeNode(var.vtype), var.chunk)
        elif isinstance(target, (Array, Deref)):
            var = self._nvar(target.target)
            assert isinstance(var.vtype, (ArrayTypeNode, PointerTypeNode))
            return ChunkVariable(var.name, var.vtype.base, var.chunk)
        else:
            raise RuntimeError()

    def _invert(self, target: Expression, initial: Any) -> Expression:
        if isinstance(target, Variable):
            assert target.variable.name == self.var.name
            return initial
        elif isinstance(target, Ref):
            return self._invert(target.target, Deref(initial, target.id))
        elif isinstance(target, (Array, Deref)):
            return self._invert(target.target, Ref(initial, target.id))
        else:
            raise RuntimeError()

    def _replace(self, target: Expression, new: Expression) -> Expression:
        if isinstance(target, Variable):
            assert target.variable.name == self.var.name
            return new
        elif isinstance(target, Lifter.VRef):
            return self._replace(target.target, new)
        elif isinstance(target, Ref):
            result = self._replace(target.target, new)
            assert isinstance(result, (Variable, Array, Deref))
            return Ref(result, target.id)
        elif isinstance(target, Deref):
            return Deref(self._replace(target.target, new), target.id)
        elif isinstance(target, Array):
            return Array(self._replace(target.target, new), target.index, target.id)
        else:
            raise RuntimeError()

    def _simplify(self, target: Any) -> Any:
        if isinstance(target, Lifter.VRef):
            return self._simplify(Ref(target.target))

        if isinstance(target, Variable):
            return target
        elif isinstance(target, Ref):
            if isinstance(target.target, Deref):
                return self._simplify(target.target.target)
            elif isinstance(target.target, Array):
                return self._simplify(target.target.target)
        elif isinstance(target, Deref):
            if isinstance(target.target, Ref):
                return self._simplify(target.target.target)
        elif isinstance(target, Array):
            if isinstance(target.target, Ref):
                return self._simplify(target.target.target)
        else:
            raise RuntimeError()

        result = self._simplify(target.target)

        if isinstance(target, Variable):
            return target
        elif isinstance(target, Ref):
            if isinstance(result, Deref):
                return result.target
            elif isinstance(result, Array):
                return result.target
            else:
                return Ref(result)
        elif isinstance(target, Deref):
            if isinstance(result, Ref):
                return result.target
            else:
                return Deref(result)
        elif isinstance(target, Array):
            if isinstance(result, Ref):
                return result.target
            else:
                return Array(result, target.index)
        else:
            raise RuntimeError()

    def _maximal(self, first: Expression, second: Expression) -> Expression:
        if isinstance(first, Ref) and isinstance(second, Ref):
            common = self._maximal(first.target, second.target)
            assert isinstance(common, (Variable, Array, Deref))
            return Ref(common)
        elif isinstance(first, Ref):
            return first
        elif isinstance(second, Ref):
            return second
        elif isinstance(first, Variable):
            return first
        elif isinstance(second, Variable):
            return second
        elif isinstance(first, Deref) and isinstance(second, Deref):
            common = self._maximal(first.target, second.target)
            return Deref(common)
        elif isinstance(first, Array) and isinstance(second, Array):
            if (
                isinstance(first.index, Value)
                and isinstance(second.index, Value)
                and first.index.value == second.index.value
            ):
                common = self._maximal(first.target, second.target)
                return Array(common, first.index)
            else:
                return self._maximal(first.target, second.target)
        elif isinstance(first, Deref) and isinstance(second, Array):
            return self._maximal(first.target, second.target)
        elif isinstance(first, Array) and isinstance(second, Deref):
            return self._maximal(first.target, second.target)
        else:
            raise RuntimeError()


def repair_calls(blocks: List[Block]) -> List[Block]:
    nblocks = {
        block.name: Block(block.name, constraint=block.constraint, known_id=block.id)
        for block in blocks
    }

    def mapper(item: BlockItem) -> BlockItem:
        if isinstance(item, Call):
            return Call(nblocks[item.block.name], known_id=item.id)
        else:
            return item

    for block in blocks:
        nblock = nblocks[block.name]
        for stmt in block.statements:
            nblock.add_statement(stmt.map(mapper))

    return list(nblocks.values())
