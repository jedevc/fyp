import random
from typing import Dict, List, Tuple


class Markov:
    def __init__(
        self, lookup: Dict[str, List[Tuple[float, str]]], size: int, terminal: str
    ):
        self.lookup = lookup

        self.size = size
        self.terminal = terminal

    def generate(self) -> str:
        complete = ""
        while True:
            ch = self._choose(complete[-self.size :])
            if ch == self.terminal:
                break

            complete += ch

        return complete

    def _choose(self, prefix: str) -> str:
        assert len(prefix) <= self.size

        sub = self.lookup[prefix]
        n = random.random()

        start = 0
        end = len(sub) - 1
        while start < end:
            i = (start + end) // 2
            if start == i:
                # assert start + 1 == end
                if n > sub[end][0]:
                    start = end
                break

            if n < sub[i][0]:
                end = i - 1
            else:
                start = i

        # if start + 1 == len(sub):
        #     assert sub[start][0] <= n
        # else:
        #     assert sub[start][0] <= n <= sub[start + 1][0]

        return sub[start][1]
