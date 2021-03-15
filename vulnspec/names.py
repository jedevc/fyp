import random
import string
from typing import Dict, Set

from .assets import Asset

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


def rename(asset: Asset, mapping: Dict[str, str]):
    for block in asset.blocks:
        if block.name in mapping:
            block.name = mapping[block.name]

    for chunk in asset.chunks:
        for var in chunk.variables:
            if var.name in mapping:
                chunk.rename_variable(var, mapping[var.name])

    for var in asset.extern.variables:
        if var.name in mapping:
            raise RuntimeError("cannot rename extern")
