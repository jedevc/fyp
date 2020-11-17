from ..parser import ChunkNode, DeclarationNode, ProcessingError, SpecNode, Visitor


class TypeCheckVisitor(Visitor):
    def __init__(self):
        super().__init__()
        self.vars = {}

    def visit_spec(self, node: SpecNode):
        for chunk in node.chunks:
            chunk.accept(self)

    def visit_chunk(self, node: ChunkNode):
        for var in node.variables:
            var.accept(self)

    def visit_declaration(self, node: DeclarationNode):
        if node.name in self.vars:
            raise ProcessingError(
                node, f"variable {node.name} cannot be declared twice"
            )

        self.vars[node.name] = node.vartype.base
