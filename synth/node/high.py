from typing import Any, List, Union

from .base import Node
from .stmt import Statement
from .types import Type


class DeclarationNode(Node):
    def __init__(self, name: str, vartype: Type):
        super().__init__()
        self.name = name
        self.vartype = vartype

    def accept(self, visitor) -> Any:
        return visitor.visit_declaration(self)


class SpecialDeclarationNode(Node):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def accept(self, visitor) -> Any:
        return visitor.visit_special_declaration(self)


class ChunkNode(Node):
    def __init__(self, variables: List[Union[DeclarationNode, SpecialDeclarationNode]]):
        super().__init__()
        self.variables = variables

    def accept(self, visitor) -> Any:
        return visitor.visit_chunk(self)


class ExternChunkNode(ChunkNode):
    def accept(self, visitor) -> Any:
        return visitor.visit_extern(self)


class BlockNode(Node):
    def __init__(self, name: str, statements: List[Statement]):
        super().__init__()
        self.name = name
        self.statements = statements

    def accept(self, visitor) -> Any:
        return visitor.visit_block(self)


class SpecNode(Node):
    def __init__(self, chunks: List[ChunkNode], blocks: List[BlockNode]):
        super().__init__()
        self.chunks = chunks
        self.blocks = blocks

    def accept(self, visitor) -> Any:
        return visitor.visit_spec(self)
