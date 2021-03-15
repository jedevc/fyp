from typing import Any, List

from ..graph import Block, BlockItem, Call


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


def find_common_prefix(lists: List[List[Any]]) -> List[Any]:
    if len(lists) == 0:
        return []

    prefix = lists[0]
    for li in lists[1:]:
        mismatch = False
        count = min(len(li), len(prefix))
        for i in range(count):
            if prefix[i] != li[i]:
                mismatch = True
                break

        if mismatch:
            prefix = prefix[:i]
        else:
            prefix = prefix[:count]

    return prefix
