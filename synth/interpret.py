import random
from functools import reduce
from typing import Any, Callable, Dict, List, Optional, Set

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

        self.chunks = chunks
        self.extern = extern

        # assign each block an interpretation
        self.func_blocks = {
            block.name
            for block in blocks
            if block.name == "main" or random.random() > 0
        }
        self.inline_blocks = {
            block.name for block in blocks if block.name not in self.func_blocks
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
        self.block_locals: Dict[str, List[Chunk]] = {}
        for chunk in self.local_chunks:
            root = traces.root(chunk, lambda bl: bl.name in self.func_blocks)
            if root is None:
                root = self.blocks["main"]

            if root.name not in self.block_locals:
                self.block_locals[root.name] = []
            self.block_locals[root.name].append(chunk)

        # determine patches to make for function blocks
        self.function_signature: Dict[str, List[ChunkVariable]] = {}
        for block, patches in traces.patches.items():
            if block.name not in self.func_blocks:
                self.function_signature[block.name] = []
                continue

            self.function_signature[block.name] = [
                patch for patch in patches if patch.chunk in self.local_chunks
            ]

        lift = Lifter()
        self.lifts: Dict[int, Expression] = {}
        self.maximals: Dict[str, Dict[str, Variable]] = {}
        for func, args in self.function_signature.items():
            self.maximals[func] = {}
            for i, arg in enumerate(args):
                maximal, narg, subs = lift.lift(self.blocks[func], arg)

                self.function_signature[func][i] = narg
                self.maximals[func][arg.name] = maximal
                self.lifts = {**self.lifts, **subs}

        # perform transformations to each block
        for blname, block in self.blocks.items():
            block = self._apply_lifts(block)
            block = self._apply_calls(block)
            self.blocks[blname] = block

    def _apply_lifts(self, block: Block) -> Block:
        def mapper(item: BlockItem) -> BlockItem:
            if item.id in self.lifts:
                return self.lifts[item.id]
            else:
                return item

        return block.map(mapper)

    def _apply_calls(self, block: Block) -> Block:
        def mapper(item: BlockItem) -> BlockItem:
            if not isinstance(item, Call):
                return item

            if item.block.name in self.func_blocks:
                if item.block.name in self.function_signature:
                    lifter = Lifter()

                    args = []
                    for arg in self.function_signature[item.block.name]:
                        target = self.maximals[item.block.name][arg.name]
                        try:
                            current = self.maximals[block.name][arg.name]
                        except KeyError:
                            for chunk in self.chunks:
                                if (var := chunk.lookup(arg.name)) :
                                    current = Variable(var)
                                    break

                        narg = lifter.dothing(target, current)
                        args.append(narg)
                else:
                    args = []

                cvar = ChunkVariable(item.block.name, None, None)
                new_stmt = ExpressionStatement(Function(Variable(cvar), args))
                return new_stmt
            elif item.block.name in self.inline_blocks:
                return StatementGroup(self.blocks[item.block.name].statements)
            else:
                raise RuntimeError()

        return block.map(mapper)

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
                    func.add_locals(chunk)

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
        self.patches[base] = []

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


class VRef(Ref):
    pass


VarContext = Expression


class Lifter:
    def __init___(self):
        pass

    def lift(self, base: Block, var: ChunkVariable):
        captures = self._capture(base, var)
        root = reduce(self._find_maximal, captures)
        root_var = self._derive_type(root)
        root_inv = self._invert_ctx(root, Variable(root_var))

        translations = {}
        for use in self._capture(base, var, False):
            translations[use.id] = self._simplify_ctx(self._replace_ctx(use, root_inv))

        return root, root_var, translations

    def dothing(self, use: VarContext, root: VarContext):
        # mainly strip down virtual-references into normal references
        # virtual references are only useful for code generating different code
        # for assignments
        use = self._simplify_ctx(use)
        root = self._simplify_ctx(root)

        root_var = self._derive_type(root)
        root_inv = self._invert_ctx(root, Variable(root_var))
        return self._simplify_ctx(self._replace_ctx(use, root_inv))

    def _capture(
        self, base: Block, var: ChunkVariable, recursive: bool = True
    ) -> List[VarContext]:
        uses: List[VarContext] = []
        stack: List[Any] = []

        def finder(part):
            if isinstance(part, Variable) and part.variable == var:
                use = part

                work = list(stack)
                while True:
                    item = work.pop()
                    if isinstance(item, Deref):
                        use = Deref(use, item.id)
                    elif isinstance(item, Ref):
                        use = Ref(use, item.id)
                    elif isinstance(item, Assignment):
                        use = VRef(use, use.id)
                    elif isinstance(item, Array):
                        use = Array(use, item.index, item.id)
                    else:
                        break

                uses.append(use)

                stack.append(part)
            else:
                stack.append(part)
                if recursive and isinstance(part, Call):
                    uses.extend(self._capture(part.block, var, True))

        base.traverse(finder)
        return uses

    def _find_maximal(self, first: VarContext, second: VarContext) -> VarContext:
        if isinstance(first, Ref) and isinstance(second, Ref):
            common = self._find_maximal(first.target, second.target)
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
            common = self._find_maximal(first.target, second.target)
            return Deref(common)
        elif isinstance(first, Array) and isinstance(second, Array):
            if (
                isinstance(first.index, Value)
                and isinstance(second.index, Value)
                and first.index.value == second.index.value
            ):
                common = self._find_maximal(first.target, second.target)
                return Array(common, first.index)
            else:
                return self._find_maximal(first.target, second.target)
        elif isinstance(first, Deref) and isinstance(second, Array):
            return self._find_maximal(first.target, second.target)
        elif isinstance(first, Array) and isinstance(second, Deref):
            return self._find_maximal(first.target, second.target)
        else:
            raise RuntimeError()

    def _derive_type(self, ctx: VarContext) -> ChunkVariable:
        if isinstance(ctx, Variable):
            return ctx.variable
        elif isinstance(ctx, Ref):
            var = self._derive_type(ctx.target)
            if var.vtype is None:
                return ChunkVariable(var.name, None, var.chunk)
            else:
                return ChunkVariable(var.name, PointerTypeNode(var.vtype), var.chunk)
        elif isinstance(ctx, (Array, Deref)):
            var = self._derive_type(ctx.target)
            assert isinstance(var.vtype, (ArrayTypeNode, PointerTypeNode))
            return ChunkVariable(var.name, var.vtype.base, var.chunk)
        else:
            raise RuntimeError()

    def _invert_ctx(self, ctx: VarContext, initial: Any) -> VarContext:
        if isinstance(ctx, Variable):
            return initial
        elif isinstance(ctx, Ref):
            return self._invert_ctx(ctx.target, Deref(initial, ctx.id))
        elif isinstance(ctx, (Array, Deref)):
            return self._invert_ctx(ctx.target, Ref(initial, ctx.id))
        else:
            raise RuntimeError()

    def _replace_ctx(self, target: VarContext, replace: VarContext) -> VarContext:
        if isinstance(target, Variable):
            return replace
        elif isinstance(target, VRef):
            return self._replace_ctx(target.target, replace)
        elif isinstance(target, Ref):
            result = self._replace_ctx(target.target, replace)
            assert isinstance(result, (Variable, Array, Deref))
            return Ref(result, target.id)
        elif isinstance(target, Deref):
            return Deref(self._replace_ctx(target.target, replace), target.id)
        elif isinstance(target, Array):
            return Array(
                self._replace_ctx(target.target, replace), target.index, target.id
            )
        else:
            raise RuntimeError()

    def _simplify_ctx(self, target: Any) -> Any:
        if isinstance(target, VRef):
            return self._simplify_ctx(Ref(target.target))

        if isinstance(target, Variable):
            return target
        elif isinstance(target, Ref):
            if isinstance(target.target, Deref):
                return self._simplify_ctx(target.target.target)
            elif isinstance(target.target, Array):
                return self._simplify_ctx(target.target.target)
        elif isinstance(target, Deref):
            if isinstance(target.target, Ref):
                return self._simplify_ctx(target.target.target)
        elif isinstance(target, Array):
            if isinstance(target.target, Ref):
                return self._simplify_ctx(target.target.target)
        else:
            raise RuntimeError()

        result = self._simplify_ctx(target.target)

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
