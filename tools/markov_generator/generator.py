import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from builtin_generator.library import Library
from builtin_generator.tags import TagKind

INCLUDE_FILE = Path(__file__).parent / "markov.py"


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("library", type=Path)
    arg_parser.add_argument("--skip-build", dest="build", action="store_false")
    args = arg_parser.parse_args()

    lib = Library("", args.library, ".", [])
    if args.build:
        lib.build()

    tags = lib.tags(headers=True, sources=True, extra_flags=["--kinds-c=+l"])

    tables = {
        "vars": MultiTable(3),
        "funcs": MultiTable(3),
    }
    table_tags = {
        TagKind.LOCAL: "vars",
        TagKind.VARIABLE: "vars",
        TagKind.FUNCTION: "funcs",
        TagKind.PROTOTYPE: "funcs",
    }

    for tag in tags:
        if tag.name.startswith("__") and tag.name.endswith("__"):
            continue
        name = tag.name.strip("_")

        if (tablename := table_tags.get(tag.kind)) :
            tables[tablename].insert(name)

    result = {name: table.dump_dict() for name, table in tables.items()}
    json.dump(result, sys.stdout, indent=4)


class Table:
    END = "$"

    def __init__(self, size: int = 1):
        self.size = size
        self.table: Dict[str, Counter[str]] = {}

        self.chars: Set[str] = set()

    def insert(self, word: str):
        word += Table.END
        for ch in word:
            self.chars.add(ch)

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

    def dump_dict(self) -> Dict[str, Any]:
        return {
            "mode": "single",
            "size": self.size,
            "terminal": Table.END,
            "table": self.construct(),
        }


class MultiTable:
    def __init__(self, max_size: int = 1):
        self.max_size = max_size
        self.tables = [Table(size) for size in range(1, max_size + 1)]

    def insert(self, word: str):
        for table in self.tables:
            table.insert(word)

    def construct(self) -> List[Dict[str, List[Tuple[float, str]]]]:
        return [table.construct() for table in self.tables]

    def dump_dict(self) -> Dict[str, Any]:
        return {
            "mode": "multi",
            "max_size": self.max_size,
            "terminal": Table.END,
            "tables": self.construct(),
        }


if __name__ == "__main__":
    main()
