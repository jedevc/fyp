import random
from typing import Tuple, TypeVar

T = TypeVar("T")


class Blocks:
    FUNCTION = 0.5
    INLINE = 0.5


class Chunks:
    LOCAL = 0.5
    GLOBAL = 0.5


class NOPs:
    TRANSFORM = 0.4
    IGNORE = 0.6


def select(*args: Tuple[float, T]) -> T:
    result = random.choices(args, weights=[arg[0] for arg in args])
    return result[0][1]
