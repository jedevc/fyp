import random
from functools import reduce
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Union

from .graph import (
    Array,
    Assignment,
    Block,
    Call,
    Chunk,
    ChunkVariable,
    Deref,
    Expression,
    ExpressionStatement,
    Function,
    FunctionDefinition,
    If,
    Lvalue,
    Program,
    Ref,
    Statement,
    Value,
    Variable,
    While,
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
        self.function_args: Dict[Block, List[ChunkVariable]] = {}
        for block, patches in traces.patches.items():
            if block not in self.func_blocks:
                continue

            self.function_args[block] = [
                patch for patch in patches if patch.chunk in self.local_chunks
            ]

        lift = Lifter()
        for func, args in self.function_args.items():
            print(func)
            for arg in args:
                lift.lift(func, arg)
            print("-----------")

    def program(self) -> Program:
        final = Program()

        for blname, block in self.blocks.items():
            if blname != "main" and block not in self.func_blocks:
                continue

            if block in self.function_args:
                func = FunctionDefinition(blname, self.function_args[block])
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
                    if stmt.block in self.function_args:
                        args = [Variable(var) for var in self.function_args[stmt.block]]
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


class Lifter:
    def __init___(self):
        pass

    def lift(self, base: Block, var: ChunkVariable) -> Expression:
        uses = self._detect(base, var)
        root = reduce(self._common, uses)
        root_var = self._var(root)
        root_inv = self._invert(root, Variable(root_var))
        print(root, root_var, root_inv)
        print(uses)
        print([self._simplify(self._replace(use, root_inv)) for use in uses])

        return None

    def _detect(self, base: Block, var: ChunkVariable) -> List[Union[Lvalue, Ref]]:
        uses: List[Union[Lvalue, Ref]] = []
        stack: List[Any] = []

        def finder(part):
            if isinstance(part, Variable) and part.variable == var:
                use = part

                work = list(stack)
                while True:
                    item = work.pop()
                    if isinstance(item, Deref):
                        use = Deref(use)
                    elif isinstance(item, Ref):
                        use = Ref(use)
                    elif isinstance(item, Assignment):
                        use = VRef(use)
                    elif isinstance(item, Array):
                        use = Array(use, item.index)
                    else:
                        break

                uses.append(use)

                stack.append(part)
            else:
                stack.append(part)
                if isinstance(part, Call):
                    uses.extend(self._detect(part.block, var))

        base.traverse(finder)
        return uses

    def _common(
        self, first: Union[Lvalue, Ref], second: Union[Lvalue, Ref]
    ) -> Union[Lvalue, Ref]:
        if isinstance(first, Ref) and isinstance(second, Ref):
            common = self._common(first.target, second.target)
            assert not isinstance(common, Ref)
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
            # HACK: this check won't be neccessary after allowing dereference
            # of expressions
            common = self._common(first.target, second.target)
            assert not isinstance(common, Ref)
            return Deref(common)
        elif isinstance(first, Array) and isinstance(second, Array):
            # HACK: this check won't be neccessary after allowing indexing into
            # expressions of expressions
            if (
                isinstance(first.index, Value)
                and isinstance(second.index, Value)
                and first.index.value == second.index.value
            ):
                common = self._common(first.target, second.target)
                assert not isinstance(common, Ref)
                return Array(common, first.index)
            else:
                return self._common(first.target, second.target)
        elif isinstance(first, Deref) and isinstance(second, Array):
            return self._common(first.target, second.target)
        elif isinstance(first, Array) and isinstance(second, Deref):
            return self._common(first.target, second.target)
        else:
            raise RuntimeError()

    def _var(self, thing: Expression) -> ChunkVariable:
        if isinstance(thing, Variable):
            return thing.variable
        elif isinstance(thing, Ref):
            var = self._var(thing.target)
            if var.vtype is None:
                return ChunkVariable(var.name, None, var.chunk)
            else:
                return ChunkVariable(var.name, PointerTypeNode(var.vtype), var.chunk)
        elif isinstance(thing, (Array, Deref)):
            var = self._var(thing.target)
            assert isinstance(var.vtype, (ArrayTypeNode, PointerTypeNode))
            return ChunkVariable(var.name, var.vtype.base, var.chunk)
        else:
            raise RuntimeError()

    def _invert(self, thing: Expression, replacement: Expression) -> Expression:
        if isinstance(thing, Variable):
            return replacement
        elif isinstance(thing, Ref):
            return self._invert(thing.target, Deref(replacement))
        elif isinstance(thing, (Array, Deref)):
            return self._invert(thing.target, Ref(replacement))
        else:
            raise RuntimeError()

    def _replace(self, target: Expression, replace: Expression) -> Expression:
        if isinstance(target, Variable):
            return replace
        elif isinstance(target, VRef):
            return self._replace(target.target, replace)
        elif isinstance(target, Ref):
            return Ref(self._replace(target.target, replace))
        elif isinstance(target, Deref):
            return Deref(self._replace(target.target, replace))
        elif isinstance(target, Array):
            return Array(self._replace(target.target, replace), target.index)
        else:
            raise RuntimeError()

    def _simplify(self, target: Lvalue) -> Lvalue:
        if isinstance(target, Variable):
            return target
        elif isinstance(target, Ref):
            if isinstance(target.target, Deref):
                return self._simplify(target.target.target)
            elif isinstance(target.target, Array):
                return self._simplify(target.target.target)
            else:
                return Ref(self._simplify(target.target))
        elif isinstance(target, Deref):
            if isinstance(target.target, Ref):
                return self._simplify(target.target.target)
            else:
                return Deref(self._simplify(target.target))
        elif isinstance(target, Array):
            if isinstance(target.target, Ref):
                return self._simplify(target.target.target)
            else:
                return Array(self._simplify(target.target), target.index)
        else:
            raise RuntimeError()
