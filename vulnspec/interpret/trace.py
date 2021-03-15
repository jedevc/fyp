from typing import Dict, List, Optional, Set

from ..graph import Block, BlockItem, Call, Chunk, ChunkVariable, Variable
from .utils import find_common_prefix


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
