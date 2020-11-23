from ..chunk import Chunk, ChunkConstraint, ChunkSet, Variable
from ..parser import (
    ChunkNode,
    DeclarationNode,
    GlobalChunkNode,
    ProcessingError,
    SpecialDeclarationNode,
    SpecNode,
    Visitor,
)


class ChunkifyVisitor(Visitor):
    def __init__(self):
        super().__init__()

        self.chunks = []
        self.globals = []

    def result(self) -> ChunkSet:
        return ChunkSet(self.globals, self.chunks)

    def visit_spec(self, node: SpecNode):
        for chunk in node.chunks:
            chunk.accept(self)

    def visit_chunk(self, node: ChunkNode):
        constraint = ChunkConstraint()
        variables = []
        for var in node.variables:
            res = var.accept(self)
            if isinstance(res, ChunkConstraint):
                constraint = constraint.join(res)
            elif isinstance(res, Variable):
                variables.append(res)
            else:
                raise RuntimeError()

        chunk = Chunk(variables, constraint)
        self.chunks.append(chunk)

    def visit_global(self, node: GlobalChunkNode):
        variables = []
        for var in node.variables:
            res = var.accept(self)
            if isinstance(res, Variable):
                variables.append(res)
            elif isinstance(res, ChunkConstraint):
                raise ProcessingError(var, "cannot process global chunk constraints")
            else:
                raise RuntimeError()

        self.globals.extend(variables)

    def visit_declaration(self, node: DeclarationNode) -> Variable:
        return Variable(node.name, node.vartype.base, node.vartype.size)

    def visit_special_declaration(
        self, node: SpecialDeclarationNode
    ) -> ChunkConstraint:
        if node.name == "eof":
            return ChunkConstraint(eof=True)
        else:
            raise ProcessingError(node, f"invalid special variable {node.name}")
