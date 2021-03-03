from typing import List, TextIO

from .block import Block, BlockItem, Call
from .chunk import Chunk


class GraphVisualizer:
    def __init__(self, blocks: List[Block], chunks: List[Chunk], extern: Chunk):
        self.blocks = blocks
        self.chunks = chunks
        self.extern = extern

    def generate_block_graph(self, output: TextIO):
        print("digraph BlockGraph {", file=output)

        for block in self.blocks:
            print(f"{block.name};", file=output)

        current = None

        def finder(part: BlockItem):
            nonlocal current
            if isinstance(part, Block):
                current = part
            elif isinstance(part, Call):
                assert current is not None
                print(f"{current.name} -> {part.block.name};", file=output)

        for block in self.blocks:
            block.traverse(finder)

        print("}", file=output)
