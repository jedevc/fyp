from ..parser import (
    AssignmentNode,
    DeclarationNode,
    ProcessingError,
    TraversalVisitor,
    VariableNode,
)


class TypeCheckVisitor(TraversalVisitor):
    def __init__(self):
        super().__init__()
        self.vars = {}

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
