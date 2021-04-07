from typing import Dict, List, Optional, Set

from ..graph import Block, BlockItem, Call, Chunk, ChunkVariable, Variable
from .utils import find_common, find_deepest


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
        self.invalid_roots: Set[Block] = set()

        self.paths: Dict[Chunk, List[List[Block]]] = {}
        self.variables: Dict[Block, Set[ChunkVariable]] = {}
        self._trace(base, [])

        self.roots: Dict[Chunk, Block] = {}

        self.patches: Dict[Block, List[ChunkVariable]] = {}
        self.patches[base] = []

        for chunk, paths in self.paths.items():
            common = set(find_common(paths))
            common = common - self.invalid_roots
            best = find_deepest(common, paths)
            if best is None:
                raise RuntimeError("no possible root block")
            self.roots[chunk] = best

            for path in paths:
                collected = set()
                subpath = path[path.index(best) + 1 :]
                for bl in reversed(subpath):
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

        return self.roots.get(chunk)

    def _trace(
        self, base: Block, prefix: List[Block], seen: Optional[Set[Block]] = None
    ):
        seen = set() if seen is None else seen

        chunks: Set[Chunk] = set()
        variables: Set[ChunkVariable] = set()

        prefix = prefix + [base]

        def finder(part: BlockItem):
            nonlocal variables

            if isinstance(part, Variable):
                if part.variable.chunk is not None:
                    chunks.add(part.variable.chunk)
                variables.add(part.variable)
            elif isinstance(part, Call):
                assert seen is not None
                if self.recursive:
                    self._trace(part.block, prefix, seen | {base})
                    variables |= self.variables[part.block]

        should_traverse = base not in self.invalid_roots
        if base in seen:
            self.invalid_roots.add(base)
        if should_traverse:
            base.traverse(finder)

        for chunk in chunks:
            if chunk not in self.paths:
                self.paths[chunk] = []
            self.paths[chunk].append(prefix)

        self.blocks.add(base)
        self.variables[base] = variables
