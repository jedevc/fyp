import random
from typing import Dict, Iterable, List, Set

from .assets import Asset
from .graph import Block, BlockItem, Call, Chunk, Variable, merge_chunks
from .interpret import Tracer
from .utils import generate_unique_name


class NopTransformer:
    def __init__(self, assets: Iterable[Asset]):
        self._blocks: List[Block] = []
        self._chunks: List[Chunk] = []
        self._extern = Chunk([])
        self._links: Dict[Block, Set[Chunk]] = {}
        for asset in assets:
            self._blocks.extend(asset.blocks)
            self._chunks.extend(asset.chunks)
            self._extern = merge_chunks(self._extern, asset.extern)
            for block in asset.blocks:
                self._links[block] = {
                    var.chunk for var in Tracer(block).variables[block] if var.chunk
                }

        self.additional_blocks: Set[Block] = set()
        self.additional_chunks: Set[Chunk] = set()
        # self.additional_extern = Chunk()

    def transform(self, target: Block) -> Block:
        def mapper(item: BlockItem) -> BlockItem:
            if not isinstance(item, Call):
                return item
            # if random.random() > 0.1:
            #     return item

            def copier(item: BlockItem):
                # we need to make each variable reference unique - since we
                # could instantiate this nop many times, in different variable
                # contexts
                if isinstance(item, Variable):
                    return Variable(item.variable)
                else:
                    return item

            # create a variation of the block
            nop = random.choice(self._blocks)
            nblock = Block(
                generate_unique_name(6), [stmt.map(copier) for stmt in nop.statements]
            )
            nblock.add_statement(item)

            self.additional_blocks.add(nblock)
            for chunk in self._links[nop]:
                self.additional_chunks.add(chunk)

            return Call(nblock)

        return target.map(mapper)
