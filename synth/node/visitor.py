from .expr import ArrayNode, DerefNode, FunctionNode, RefNode, ValueNode, VariableNode
from .high import (
    BlockNode,
    ChunkNode,
    DeclarationNode,
    ExternChunkNode,
    SpecialDeclarationNode,
    SpecNode,
)
from .stmt import AssignmentNode, CallNode, ExpressionStatementNode, IfNode
from .types import ArrayTypeNode, FuncTypeNode, PointerTypeNode, SimpleTypeNode


class Visitor:
    def __init__(self):
        pass

    def visit_spec(self, node: SpecNode):
        pass

    def visit_chunk(self, node: ChunkNode):
        pass

    def visit_extern(self, node: ExternChunkNode):
        pass

    def visit_block(self, node: BlockNode):
        pass

    def visit_declaration(self, node: DeclarationNode):
        pass

    def visit_special_declaration(self, node: SpecialDeclarationNode):
        pass

    def visit_type_simple(self, node: SimpleTypeNode):
        pass

    def visit_type_pointer(self, node: PointerTypeNode):
        pass

    def visit_type_array(self, node: ArrayTypeNode):
        pass

    def visit_type_func(self, node: FuncTypeNode):
        pass

    def visit_assignment(self, node: AssignmentNode):
        pass

    def visit_variable(self, node: VariableNode):
        pass

    def visit_ref(self, node: RefNode):
        pass

    def visit_deref(self, node: DerefNode):
        pass

    def visit_array(self, node: ArrayNode):
        pass

    def visit_function(self, node: FunctionNode):
        pass

    def visit_value(self, node: ValueNode):
        pass

    def visit_call(self, node: CallNode):
        pass

    def visit_if(self, node: IfNode):
        pass

    def visit_exprstmt(self, node: ExpressionStatementNode):
        pass


class TraversalVisitor(Visitor):
    """
    A basic visitor to traverse all the nodes in the AST.

    This is indended to be easily overridden, so as to more easily reach the
    nodes of interest.
    """

    def visit_spec(self, node: SpecNode):
        for chunk in node.chunks:
            chunk.accept(self)
        for block in node.blocks:
            block.accept(self)

    def visit_chunk(self, node: ChunkNode):
        for var in node.variables:
            var.accept(self)

    def visit_extern(self, node: ExternChunkNode):
        for var in node.variables:
            var.accept(self)

    def visit_block(self, node: BlockNode):
        for stmt in node.statements:
            stmt.accept(self)

    def visit_declaration(self, node: DeclarationNode):
        node.vartype.accept(self)

    def visit_special_declaration(self, node: SpecialDeclarationNode):
        pass

    def visit_type_simple(self, node: SimpleTypeNode):
        pass

    def visit_type_pointer(self, node: PointerTypeNode):
        pass

    def visit_type_array(self, node: ArrayTypeNode):
        pass

    def visit_type_func(self, node: FuncTypeNode):
        pass

    def visit_assignment(self, node: AssignmentNode):
        node.target.accept(self)
        node.expression.accept(self)

    def visit_ref(self, node: RefNode):
        node.target.accept(self)

    def visit_deref(self, node: DerefNode):
        node.target.accept(self)

    def visit_array(self, node: ArrayNode):
        node.target.accept(self)
        node.index.accept(self)

    def visit_variable(self, node: VariableNode):
        pass

    def visit_function(self, node: FunctionNode):
        for arg in node.arguments:
            arg.accept(self)

    def visit_value(self, node: ValueNode):
        pass

    def visit_call(self, node: CallNode):
        pass

    def visit_if(self, node: IfNode):
        node.condition.accept(self)
        for statement in node.statements:
            statement.accept(self)

    def visit_exprstmt(self, node: ExpressionStatementNode):
        node.expression.accept(self)
