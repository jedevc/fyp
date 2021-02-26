import random
from typing import Dict, Iterable, List, Set

from .assets import Asset
from .graph import Block, BlockItem, Call, Chunk
from .interpret import Tracer
from .utils import generate_unique_name


class NopTransformer:
    def __init__(self, assets: Iterable[Asset]):
        self._blocks: List[Block] = []
        self._chunk_links: Dict[Block, Set[Chunk]] = {}
        self._extern_links: Dict[Block, Set[Chunk]] = {}
        for asset in assets:
            self._blocks.extend(asset.blocks)
            for block in asset.blocks:
                self._chunk_links[block] = {
                    var.chunk
                    for var in Tracer(block).variables[block]
                    if var.chunk and var.chunk in asset.chunks
                }
                self._extern_links[block] = {
                    var.chunk
                    for var in Tracer(block).variables[block]
                    if var.chunk and var in asset.extern.variables
                }

        self.additional_blocks: Set[Block] = set()
        self.additional_chunks: Set[Chunk] = set()
        self.additional_externs: Set[Chunk] = set()

    def transform(self, target: Block) -> Block:
        def mapper(item: BlockItem) -> BlockItem:
            if not isinstance(item, Call):
                return item
            if random.random() > 1.0:
                return item

            def copier(item: BlockItem):
                # We need to make each variable reference unique - since we
                # could instantiate this nop many times, in different variable
                # contexts
                # Also, it's just good practice to have every ID different,
                # hopefully avoiding future problems!
                item.id = BlockItem.new_id()
                return item

            # create a variation of the block
            nop = random.choice(self._blocks)
            nblock = Block(
                generate_unique_name(6),
                [stmt.map(copier) for stmt in nop.statements],
                nop.constraint,
            )
            nblock.add_statement(item)

            self.additional_blocks.add(nblock)
            for chunk in self._chunk_links[nop]:
                self.additional_chunks.add(chunk)
            for extern in self._extern_links[nop]:
                self.additional_externs.add(extern)

            return Call(nblock)

        return target.map(mapper)
