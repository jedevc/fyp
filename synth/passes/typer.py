from ..parser import (
    AssignmentNode,
    BlockNode,
    ChunkNode,
    DeclarationNode,
    FunctionNode,
    GlobalChunkNode,
    ProcessingError,
    SpecNode,
    VariableNode,
    Visitor,
)


class TypeCheckVisitor(Visitor):
    def __init__(self):
        super().__init__()
        self.vars = {}

    def visit_spec(self, node: SpecNode):
        for chunk in node.chunks:
            chunk.accept(self)
        for block in node.blocks:
            block.accept(self)

    def visit_chunk(self, node: ChunkNode):
        for var in node.variables:
            var.accept(self)

    def visit_global(self, node: GlobalChunkNode):
        for var in node.variables:
            var.accept(self)

    def visit_function(self, node: FunctionNode):
        for arg in node.arguments:
            arg.accept(self)

    def visit_declaration(self, node: DeclarationNode):
        if node.name in self.vars:
            raise ProcessingError(
                node, f"variable {node.name} cannot be declared twice"
            )

        self.vars[node.name] = node.vartype.base

    def visit_block(self, node: BlockNode):
        for statement in node.statements:
            statement.accept(self)

    def visit_assignment(self, node: AssignmentNode):
        if node.target not in self.vars:
            raise ProcessingError(node, f"variable {node.target} has not been declared")

        node.expression.accept(self)

    def visit_variable(self, node: VariableNode):
        if node.name not in self.vars:
            raise ProcessingError(node, f"variable {node.name} has not been declared")
