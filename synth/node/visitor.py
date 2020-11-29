from typing import Any

from .expr import *  # pylint: disable=wildcard-import,unused-wildcard-import
from .high import *  # pylint: disable=wildcard-import,unused-wildcard-import
from .stmt import *  # pylint: disable=wildcard-import,unused-wildcard-import
from .types import *  # pylint: disable=wildcard-import,unused-wildcard-import


class Visitor:
    def __init__(self):
        pass

    def visit_spec(self, node: SpecNode) -> Any:
        pass

    def visit_chunk(self, node: ChunkNode) -> Any:
        pass

    def visit_extern(self, node: ExternChunkNode) -> Any:
        pass

    def visit_block(self, node: BlockNode) -> Any:
        pass

    def visit_declaration(self, node: DeclarationNode) -> Any:
        pass

    def visit_special_declaration(self, node: SpecialDeclarationNode) -> Any:
        pass

    def visit_type_simple(self, node: SimpleTypeNode) -> Any:
        pass

    def visit_type_pointer(self, node: PointerTypeNode) -> Any:
        pass

    def visit_type_array(self, node: ArrayTypeNode) -> Any:
        pass

    def visit_type_func(self, node: FuncTypeNode) -> Any:
        pass

    def visit_assignment(self, node: AssignmentNode) -> Any:
        pass

    def visit_variable(self, node: VariableNode) -> Any:
        pass

    def visit_ref(self, node: RefNode) -> Any:
        pass

    def visit_deref(self, node: DerefNode) -> Any:
        pass

    def visit_array(self, node: ArrayNode) -> Any:
        pass

    def visit_function(self, node: FunctionNode) -> Any:
        pass

    def visit_value(self, node: ValueNode) -> Any:
        pass

    def visit_call(self, node: CallNode) -> Any:
        pass

    def visit_if(self, node: IfNode) -> Any:
        pass

    def visit_exprstmt(self, node: ExpressionStatementNode) -> Any:
        pass


class TraversalVisitor(Visitor):
    """
    A basic visitor to traverse all the nodes in the AST.

    This is indended to be easily overridden, so as to more easily reach the
    nodes of interest.
    """

    def visit_spec(self, node: SpecNode) -> Any:
        for chunk in node.chunks:
            chunk.accept(self)
        for block in node.blocks:
            block.accept(self)

    def visit_chunk(self, node: ChunkNode) -> Any:
        for var in node.variables:
            var.accept(self)

    def visit_extern(self, node: ExternChunkNode) -> Any:
        for var in node.variables:
            var.accept(self)

    def visit_block(self, node: BlockNode) -> Any:
        for stmt in node.statements:
            stmt.accept(self)

    def visit_declaration(self, node: DeclarationNode) -> Any:
        node.vartype.accept(self)

    def visit_special_declaration(self, node: SpecialDeclarationNode) -> Any:
        pass

    def visit_type_simple(self, node: SimpleTypeNode) -> Any:
        pass

    def visit_type_pointer(self, node: PointerTypeNode) -> Any:
        pass

    def visit_type_array(self, node: ArrayTypeNode) -> Any:
        pass

    def visit_type_func(self, node: FuncTypeNode) -> Any:
        pass

    def visit_assignment(self, node: AssignmentNode) -> Any:
        node.target.accept(self)
        node.expression.accept(self)

    def visit_ref(self, node: RefNode) -> Any:
        node.target.accept(self)

    def visit_deref(self, node: DerefNode) -> Any:
        node.target.accept(self)

    def visit_array(self, node: ArrayNode) -> Any:
        node.target.accept(self)
        node.index.accept(self)

    def visit_variable(self, node: VariableNode) -> Any:
        pass

    def visit_function(self, node: FunctionNode) -> Any:
        for arg in node.arguments:
            arg.accept(self)

    def visit_value(self, node: ValueNode) -> Any:
        pass

    def visit_call(self, node: CallNode) -> Any:
        pass

    def visit_if(self, node: IfNode) -> Any:
        node.condition.accept(self)
        for statement in node.statements:
            statement.accept(self)

    def visit_exprstmt(self, node: ExpressionStatementNode) -> Any:
        node.expression.accept(self)
