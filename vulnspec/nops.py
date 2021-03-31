import random
from functools import reduce
from typing import Dict, Iterable, List, Set

from .assets import Asset
from .common.error import SynthError
from .common.names import generate_unique_name
from .graph import Block, BlockItem, Call, Chunk, merge_chunks
from .interpret import Tracer, repair_calls


class NopTransformError(SynthError):
    pass


class NopTransformer:
    def __init__(self, assets: Iterable[Asset]):
        self._blocks: List[Block] = []
        self._names: Set[str] = set()

        self._chunk_links: Dict[Block, Set[Chunk]] = {}
        self._extern_links: Dict[Block, Set[Chunk]] = {}

        for asset in assets:
            have_added = False
            for block in asset.blocks:
                if block.constraint.nop:
                    have_added = True
                else:
                    continue

                self._blocks.append(block)
                self._names.add(block.name)

                block_vars = Tracer(block).variables[block]
                self._chunk_links[block] = {
                    var.chunk
                    for var in block_vars
                    if var.chunk and var.chunk in asset.chunks
                }
                self._extern_links[block] = {
                    var.chunk
                    for var in block_vars
                    if var.chunk and var in asset.extern.variables
                }

            if not have_added:
                raise RuntimeError("no nops were loaded from asset")

            for chunk in asset.chunks:
                for var in chunk.variables:
                    self._names.add(var.name)

        if len(self._blocks) == 0:
            raise RuntimeError("no assets were found")

    def transform(self, asset: Asset) -> Asset:
        # check for name collisions
        for block in asset.blocks:
            if block.name in self._names:
                raise NopTransformError(
                    f"name {block.name} in asset was already declared in NOP"
                )
        for chunk in asset.chunks:
            for var in chunk.variables:
                if var.name in self._names:
                    raise NopTransformError(
                        f"name {var.name} in asset was already declared in NOP"
                    )

        additional_blocks: Set[Block] = set()
        additional_chunks: Set[Chunk] = set()
        additional_externs: Set[Chunk] = set()

        nop_names: Dict[str, str] = {}

        def mapper(item: BlockItem) -> BlockItem:
            if not isinstance(item, Call):
                return item
            if random.random() > 1.0:
                return item

            # create a variation of the block
            nop = random.choice(self._blocks)
            nblock = Block(
                generate_unique_name(6),
                [stmt.map(copier) for stmt in nop.statements],
                nop.constraint,
            )
            nblock.add_statement(item)

            nop_names[nblock.name] = nop.name

            additional_blocks.add(nblock)
            for chunk in self._chunk_links[nop]:
                additional_chunks.add(chunk)
            for extern in self._extern_links[nop]:
                additional_externs.add(extern)

            return Call(nblock)

        blocks = [block.map(mapper) for block in asset.blocks] + list(additional_blocks)
        blocks = repair_calls(blocks)
        chunks = asset.chunks + list(additional_chunks)
        extern = reduce(merge_chunks, [asset.extern, *additional_externs])

        final = Asset(asset.name, blocks, chunks, extern)
        final.attachments = dict(asset.attachments)
        final.attachments["nops"] = nop_names
        return final


def copier(item: BlockItem):
    # We need to make each variable reference unique - since we
    # could instantiate this nop many times, in different variable
    # contexts
    # Also, it's just good practice to have every ID different,
    # hopefully avoiding future problems!
    item.id = BlockItem.new_id()
    return item
