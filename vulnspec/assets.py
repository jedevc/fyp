from io import TextIOWrapper
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, TextIO, Union

from .common.dump import DumpType
from .graph import Block, Chunk
from .parser import Lexer, Parser
from .parser.token import TokenType
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
        self,
        name: str,
        blocks: List[Block],
        chunks: List[Chunk],
        extern: Chunk,
        includes: List[str],
    ):
        self.name = name

        self.blocks = blocks
        self.chunks = chunks
        self.extern = extern

        self.includes = includes

        self.attachments: Dict[str, Any] = {}

    @staticmethod
    def load(
        source: Union[str, TextIO, Path],
        external: bool = False,
        templates: Optional[Dict[str, Union[str, int, float, bool]]] = None,
        dump: Optional[Dict[DumpType, Optional[Path]]] = None,
    ) -> "Asset":
        if isinstance(source, str):
            return Asset._load(
                "", source, external=external, templates=templates, dump=dump
            )
        elif isinstance(source, Path):
            return Asset._load(
                str(source),
                source.read_text(),
                external=external,
                templates=templates,
                dump=dump,
            )
        elif isinstance(source, TextIOWrapper):
            return Asset._load(
                source.name,
                source.read(),
                external=external,
                templates=templates,
                dump=dump,
            )
        else:
            raise TypeError()

    @staticmethod
    def _load(
        name: str,
        stream: str,
        external: bool = False,
        templates: Optional[Dict[str, Union[str, int, float, bool]]] = None,
        dump: Optional[Dict[DumpType, Optional[Path]]] = None,
    ) -> "Asset":
        lex = Lexer(stream)
        tokens = lex.tokens_list()
        if dump and (output := dump.get(DumpType.Tokens)):
            with output.open("w") as f:
                for token in tokens:
                    if token.ttype in (TokenType.Newline, TokenType.EOF):
                        print(token.show(), file=f)
                    else:
                        print(token.show(), end=", ", file=f)

        parser = Parser(tokens)
        spec = parser.parse()
        if dump and (output := dump.get(DumpType.AST)):
            with output.open("w") as f:
                printer = PrinterVisitor(f)
                spec.accept(printer)
        if dump and (output := dump.get(DumpType.ASTDiagram)):
            with output.open("w") as f:
                visualizer = VisualizerVisitor(f)
                spec.accept(visualizer)

        template_visitor = TemplaterVisitor(templates)
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

        asset = Asset(name, blocks, chunks, extern, spec.includes)
        asset.attachments["templates"] = template_visitor.instantiations
        return asset


class AssetLoader:
    def __init__(self, root: Path, extension: str = "spec"):
        self.root = root
        self.extension = extension

    def list(self, external: bool = False) -> Iterable[Asset]:
        for path in self.root.glob(f"**/*.{self.extension}"):
            yield Asset.load(path, external=external)
