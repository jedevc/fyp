from typing import Collection, Iterable, List, Optional, Sequence, TypeVar

from ..graph import Block, BlockItem, Call

T = TypeVar("T")


def repair_calls(blocks: Collection[Block]) -> List[Block]:
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


def find_common(lists: Sequence[Collection[T]]) -> Iterable[T]:
    if len(lists) == 0:
        return

    primary, others = lists[0], lists[1:]

    for item in primary:
        valid = True
        for other in others:
            if item not in other:
                valid = False
                break

        if valid:
            yield item


def find_deepest(items: Collection[T], lists: Sequence[Sequence[T]]) -> Optional[T]:
    if len(items) == 0:
        return None

    primary = lists[0]
    for item in reversed(primary):
        if item in items:
            return item

    raise AssertionError()
