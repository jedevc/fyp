import json
import random
from typing import Any, Dict, List, Set, Tuple

from .builtins import functions, types, variables
from .common.data import data_path
from .parser.token import RESERVED_WORDS


class MarkovLoader:
    def __init__(self):
        with data_path("markov.json").open() as f:
            self.data = json.load(f)

    def model(self, name: str, size: Tuple[int, int]):
        return self._create(self.data[name], size)

    def _create(self, model: Dict[Any, Any], size: Tuple[int, int]) -> "MarkovWrapper":
        if model["mode"] == "single":
            markov = Markov(model["table"], model["size"], model["terminal"])
        elif model["mode"] == "multi":
            markov = MultiMarkov(model["tables"], model["max_size"], model["terminal"])
        else:
            raise KeyError()

        return MarkovWrapper(markov, size)


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
            ch = self.choose(complete)
            if ch == self.terminal:
                break

            complete += ch

        return complete

    def choose(self, prefix: str) -> str:
        prefix = prefix[-self.size :]
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


class MultiMarkov(Markov):
    def __init__(
        self,
        lookups: List[Dict[str, List[Tuple[float, str]]]],
        max_size: int,
        terminal: str,
    ):
        super().__init__({}, max_size, terminal)

        self.markovs = [
            Markov(lookup, i + 1, terminal) for i, lookup in enumerate(lookups)
        ]
        assert len(self.markovs) == self.size

    def choose(self, prefix: str) -> str:
        while True:
            markov = self.markovs[int(random.triangular(0, len(self.markovs)))]
            try:
                return markov.choose(prefix)
            except KeyError:
                # oh boi
                continue


class MarkovWrapper:
    def __init__(self, markov: Markov, size_range: Tuple[int, int]):
        self.markov = markov

        self.min_size, self.max_size = size_range

        self._exclude: Set[str] = set()

    def generate(self) -> str:
        while True:
            result = self.markov.generate()
            if not self.min_size <= len(result) <= self.max_size:
                continue
            if result in self._exclude:
                continue
            if result in RESERVED_WORDS:
                continue
            if result in ("argc", "argv"):
                continue
            if (
                result in types.TRANSLATIONS
                or result in functions.TRANSLATIONS
                or result in variables.TRANSLATIONS
            ):
                continue

            break

        self._exclude.add(result)
        return result
