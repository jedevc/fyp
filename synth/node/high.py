from typing import List, Optional, Union

from .base import Node, X
from .expr import ExpressionNode
from .stmt import StatementNode
from .types import TypeNode
from .visitor import Visitor


class DeclarationNode(Node):
    def __init__(
        self, name: str, vartype: TypeNode, initial: Optional[ExpressionNode] = None
    ):
        super().__init__()
        self.name = name
        self.vartype = vartype
        self.initial = initial

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_declaration(self)


class SpecialDeclarationNode(Node):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_special_declaration(self)


class ChunkNode(Node):
    def __init__(self, variables: List[Union[DeclarationNode, SpecialDeclarationNode]]):
        super().__init__()
        self.variables = variables

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_chunk(self)


class ExternChunkNode(ChunkNode):
    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_extern(self)


class BlockNode(Node):
    def __init__(self, name: str, statements: List[StatementNode]):
        super().__init__()
        self.name = name
        self.statements = statements

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_block(self)


class SpecNode(Node):
    def __init__(self, chunks: List[ChunkNode], blocks: List[BlockNode]):
        super().__init__()
        self.chunks = chunks
        self.blocks = blocks

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_spec(self)
