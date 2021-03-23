import random
import string
from typing import Dict, Set

from ..assets import Asset
from ..graph import BlockItem, ChunkVariable, FunctionDefinition, Variable

_names: Set[str] = set()


def generate_name(length: int) -> str:
    return "".join(random.choice(string.ascii_letters) for i in range(length))


def generate_unique_name(length: int) -> str:
    while True:
        name = generate_name(length)
        if name not in _names:
            break

    _names.add(name)
    return name


def rename_blocks(asset: Asset, mapping: Dict[str, str]):
    for block in asset.blocks:
        if block.name in mapping:
            block.name = mapping[block.name]


def rename_vars(asset: Asset, mapping: Dict[str, str]):
    for chunk in asset.chunks:
        for var in chunk.variables:
            if var.name in mapping:
                chunk.rename_variable(var, mapping[var.name])

    for var in asset.extern.variables:
        if var.name in mapping:
            raise RuntimeError("cannot rename extern")

    # traverse the block graph (to get all those chunk-less variables)
    def traverser(item: BlockItem):
        if isinstance(item, Variable):
            if item.variable.name in mapping:
                item.variable.name = mapping[item.variable.name]

    for block in asset.blocks:
        block.traverse(traverser)


def rename_args(func: FunctionDefinition, mapping: Dict[str, str]):
    nargs: Dict[str, ChunkVariable] = {}

    for i, arg in enumerate(func.args):
        if arg.name not in mapping:
            continue

        narg = ChunkVariable(mapping[arg.name], arg.vtype, None)
        nargs[arg.name] = narg
        func.args[i] = narg

    def mapper(item: BlockItem) -> BlockItem:
        if isinstance(item, Variable):
            print(item.variable.name)

        if isinstance(item, Variable) and item.variable.name in nargs:
            return Variable(nargs[item.variable.name])
        else:
            return item

    for i, stmt in enumerate(func.statements):
        func.statements[i] = stmt.map(mapper)
