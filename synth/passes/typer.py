from ..parser import (
    AssignmentNode,
    BlockNode,
    CallNode,
    DeclarationNode,
    ProcessingError,
    SpecNode,
    TraversalVisitor,
    VariableNode,
)


class TypeCheckVisitor(TraversalVisitor):
    def __init__(self):
        super().__init__()
        self.vars = {}

        self.blocks = {}
        self.block_refs = {}

    def visit_spec(self, node: SpecNode):
        super().visit_spec(node)

        # resolve block references after traversal
        for block_name in self.block_refs:
            if block_name not in self.blocks:
                raise ProcessingError(
                    self.block_refs[block_name], f"block {block_name} is not defined"
                )

    def visit_block(self, node: BlockNode):
        if node.name in self.blocks:
            raise ProcessingError(node, f"block {node.name} cannot be defined twice")

        self.blocks[node.name] = node

        super().visit_block(node)

    def visit_call(self, node: CallNode):
        self.block_refs[node.target] = node

        super().visit_call(node)

    def visit_declaration(self, node: DeclarationNode):
        if node.name in self.vars:
            raise ProcessingError(
                node, f"variable {node.name} cannot be declared twice"
            )

        self.vars[node.name] = node.vartype.base

        super().visit_declaration(node)

    def visit_assignment(self, node: AssignmentNode):
        if node.target not in self.vars:
            raise ProcessingError(node, f"variable {node.target} has not been declared")

        super().visit_assignment(node)

    def visit_variable(self, node: VariableNode):
        if node.name not in self.vars:
            raise ProcessingError(node, f"variable {node.name} has not been declared")

        super().visit_variable(node)
