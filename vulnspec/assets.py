from io import TextIOWrapper
from pathlib import Path
from typing import Dict, Iterable, List, Optional, TextIO, Union

from .dump import DumpType
from .graph import Block, Chunk
from .parser import Lexer, Parser
from .passes import (
    BlockifyVisitor,
    ChunkifyVisitor,
    PrinterVisitor,
    TemplaterVisitor,
    TypeCheckVisitor,
    VisualizerVisitor,
)


class Asset:
    def __init__(
        self, name: str, blocks: List[Block], chunks: List[Chunk], extern: Chunk
    ):
        self.name = name

        self.blocks = blocks
        self.chunks = chunks
        self.extern = extern

    @staticmethod
    def load(
        source: Union[str, TextIO, Path],
        external: bool = False,
        dump: Optional[Dict[DumpType, Optional[TextIO]]] = None,
    ) -> "Asset":
        if isinstance(source, str):
            return Asset._load("", source, external=external, dump=dump)
        elif isinstance(source, Path):
            return Asset._load(
                str(source), source.read_text(), external=external, dump=dump
            )
        elif isinstance(source, TextIOWrapper):
            return Asset._load(source.name, source.read(), external=external, dump=dump)
        else:
            raise TypeError()

    @staticmethod
    def _load(
        name: str,
        stream: str,
        external: bool = False,
        dump: Optional[Dict[DumpType, Optional[TextIO]]] = None,
    ) -> "Asset":
        lex = Lexer(stream)
        tokens = lex.tokens_list()

        parser = Parser(tokens)
        spec = parser.parse()
        if dump and (output := dump.get(DumpType.AST)):
            printer = PrinterVisitor(output)
            spec.accept(printer)
        if dump and (output := dump.get(DumpType.ASTDiagram)):
            visualizer = VisualizerVisitor(output)
            spec.accept(visualizer)

        template_visitor = TemplaterVisitor()
        spec.accept(template_visitor)

        type_visitor = TypeCheckVisitor(require_main=not external)
        spec.accept(type_visitor)

        chunk_visitor = ChunkifyVisitor()
        spec.accept(chunk_visitor)
        chunks = chunk_visitor.chunks
        extern = chunk_visitor.extern

        block_visitor = BlockifyVisitor(chunks, extern)
        spec.accept(block_visitor)
        blocks = block_visitor.result()

        return Asset(name, blocks, chunks, extern)


class AssetLoader:
    EXTENSION = "spec"
    ROOT = Path(__file__).parent.parent / "assets"

    @staticmethod
    def list(*category: str, external: bool = False) -> Iterable[Asset]:
        current = AssetLoader.ROOT
        for part in category:
            current /= part

        for path in current.glob(f"**/*.{AssetLoader.EXTENSION}"):
            yield Asset.load(path, external=external)
