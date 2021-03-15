import json
from typing import Any, List, Set, TextIO, Tuple

from ..interpret.trace import Tracer
from .block import Block, BlockItem, Call
from .chunk import Chunk


class GraphVisualizer:
    def __init__(self, output: TextIO):
        self.output = output

        self._nodes: Set[str] = set()
        self._lines: Set[Tuple[str, str]] = set()

    def generate_block_graph(
        self, blocks: List[Block], chunks: List[Chunk], extern: Chunk
    ):  # pylint: disable=unused-argument
        with self._scope("digraph BlockGraph"):
            for block in blocks:
                self._node(block.name)

            current = None

            def finder(part: BlockItem):
                nonlocal current
                if isinstance(part, Block):
                    current = part
                elif isinstance(part, Call):
                    assert current is not None
                    self._line(current.name, part.block.name)

            for block in blocks:
                block.traverse(finder)

    def generate_block_chunk_graph(
        self, blocks: List[Block], chunks: List[Chunk], extern: Chunk
    ):  # pylint: disable=unused-argument
        with self._scope("digraph BlockChunkGraph"):
            for i, chunk in enumerate(chunks):
                for var in chunk.variables:
                    self._node(var.name, shape="note", label=json.dumps(var.typename()))

                with self._scope(f"subgraph clusterChunk{i}"):
                    self._raw('style="dotted,bold";')
                    for var in chunk.variables:
                        self._node(var.name)

            for block in blocks:
                self._node(block.name)

            current = None

            def finder(part: BlockItem):
                nonlocal current
                if isinstance(part, Block):
                    current = part
                elif isinstance(part, Call):
                    assert current is not None
                    self._line(current.name, part.block.name)

            for block in blocks:
                block.traverse(finder)

                trace = Tracer(block, recursive=False)
                for var in trace.variables[block]:
                    self._line(block.name, var.name, style="dotted")

    def _scope(self, title: str) -> Any:
        output = self.output

        class Scope:
            def __enter__(self):
                print(title + "{", file=output)

            def __exit__(self, *args, **kwargs):
                print("}", file=output)

        return Scope()

    def _line(self, start: str, end: str, **kwargs):
        if (start, end) in self._lines:
            return
        self._lines.add((start, end))

        base = f"{json.dumps(start)} -> {json.dumps(end)}"
        if kwargs:
            args = ", ".join(f"{lhs}={rhs}" for lhs, rhs in kwargs.items())
            print(f"{base}[{args}];", file=self.output)
        else:
            print(f"{base};", file=self.output)

    def _node(self, name: str, **kwargs):
        if name in self._nodes:
            return
        self._nodes.add(name)

        base = f"{json.dumps(name)}"
        if kwargs:
            args = ", ".join(f"{lhs}={rhs}" for lhs, rhs in kwargs.items())
            print(f"{base}[{args}];", file=self.output)
        else:
            print(f"{base};", file=self.output)

    def _raw(self, raw: str):
        print(raw, file=self.output)
