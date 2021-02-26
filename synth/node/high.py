from typing import List, Optional

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


class ChunkNode(Node):
    def __init__(self, variables: List[DeclarationNode], constraints: List[str]):
        super().__init__()
        self.variables = variables
        self.constraints = constraints

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_chunk(self)


class ExternChunkNode(ChunkNode):
    def __init__(self, variables: List[DeclarationNode]):
        super().__init__(variables, [])

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_extern(self)


class BlockNode(Node):
    def __init__(
        self, name: str, statements: List[StatementNode], constraints: List[str]
    ):
        super().__init__()
        self.name = name
        self.statements = statements
        self.constraints = constraints

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_block(self)


class SpecNode(Node):
    def __init__(self, chunks: List[ChunkNode], blocks: List[BlockNode]):
        super().__init__()
        self.chunks = chunks
        self.blocks = blocks

    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_spec(self)
