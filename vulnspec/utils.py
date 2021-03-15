from typing import Any, List


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
