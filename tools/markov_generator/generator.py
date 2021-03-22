import argparse
import io
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

import black
from builtin_generator.library import Library
from builtin_generator.tags import TagKind


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("library", type=Path)
    arg_parser.add_argument("--skip-build", dest="build", action="store_false")
    args = arg_parser.parse_args()

    lib = Library("", args.library, ".")
    if args.build:
        lib.build()

    table = Table(2)

    tags = lib.tags(headers=True, sources=True, extra_flags=["--kinds-c=+l"])
    for tag in tags:
        if tag.name.startswith("__") and tag.name.endswith("__"):
            continue

        if tag.kind == TagKind.LOCAL:
            table.insert(tag.name)

    output = io.StringIO()

    print(f"TERMINATOR = '{Table.END}'", file=output)
    print(f"SIZE = {table.size}", file=output)
    print(f"CHARS = '{table.chars}'", file=output)
    print(f"TABLE = {table.construct()}", file=output)

    final = output.getvalue()
    try:
        final = black.format_file_contents(final, fast=True, mode=black.Mode(()))
    except black.NothingChanged:
        pass

    print(
        "\n".join(
            [
                "'''",
                f"This file was autogenerated by markov_generator at {datetime.now()}.",
                "",
                "DO NOT MODIFY IT MANUALLY!",
                "'''",
            ]
        )
        + "\n"
    )
    print(final)


class Table:
    END = "$"

    def __init__(self, size: int = 1):
        self.size = size
        self.table: Dict[str, Counter[str]] = {}
        self._chars: Set[str] = set()

    @property
    def chars(self):
        return "".join(sorted(self._chars))

    def insert(self, word: str):
        word += Table.END
        for ch in word:
            self._chars.add(ch)

        for j in range(len(word)):
            i = max(0, j - self.size)
            key = word[i:j]
            value = word[j]

            if key not in self.table:
                self.table[key] = Counter()
            self.table[key][value] += 1

    def construct(self) -> Dict[str, List[Tuple[float, str]]]:
        result: Dict[str, List[Tuple[float, str]]] = {}
        for key in self.table:
            total = sum(self.table[key].values())
            running = 0.0
            pieces = []
            for value, score in self.table[key].items():
                pieces.append((running, value))
                running += score / total

            result[key] = pieces

        return result


if __name__ == "__main__":
    main()
