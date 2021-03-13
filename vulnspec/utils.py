import random
import string
from typing import Any, List, Set


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
