from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from .base import Node
    from .expr import (
        ArrayNode,
        BinaryOperationNode,
        DerefNode,
        FunctionNode,
        RefNode,
        ValueNode,
        VariableNode,
    )
    from .high import (
        BlockNode,
        ChunkNode,
        DeclarationNode,
        ExternChunkNode,
        SpecialDeclarationNode,
        SpecNode,
    )
    from .stmt import (
        AssignmentNode,
        CallNode,
        ExpressionStatementNode,
        IfNode,
        SplitNode,
        WhileNode,
    )
    from .types import ArrayTypeNode, FuncTypeNode, PointerTypeNode, SimpleTypeNode

T = TypeVar("T")


class Visitor(Generic[T]):
    def __init__(self):
        pass

    def visit_spec(self, node: "SpecNode") -> T:
        pass

    def visit_chunk(self, node: "ChunkNode") -> T:
        pass

    def visit_extern(self, node: "ExternChunkNode") -> T:
        pass

    def visit_block(self, node: "BlockNode") -> T:
        pass

    def visit_declaration(self, node: "DeclarationNode") -> T:
        pass

    def visit_special_declaration(self, node: "SpecialDeclarationNode") -> T:
        pass

    def visit_type_simple(self, node: "SimpleTypeNode") -> T:
        pass

    def visit_type_pointer(self, node: "PointerTypeNode") -> T:
        pass

    def visit_type_array(self, node: "ArrayTypeNode") -> T:
        pass

    def visit_type_func(self, node: "FuncTypeNode") -> T:
        pass

    def visit_assignment(self, node: "AssignmentNode") -> T:
        pass

    def visit_variable(self, node: "VariableNode") -> T:
        pass

    def visit_ref(self, node: "RefNode") -> T:
        pass

    def visit_deref(self, node: "DerefNode") -> T:
        pass

    def visit_array(self, node: "ArrayNode") -> T:
        pass

    def visit_binary(self, node: "BinaryOperationNode") -> T:
        pass

    def visit_function(self, node: "FunctionNode") -> T:
        pass

    def visit_value(self, node: "ValueNode") -> T:
        pass

    def visit_call(self, node: "CallNode") -> T:
        pass

    def visit_split(self, node: "SplitNode") -> T:
        pass

    def visit_if(self, node: "IfNode") -> T:
        pass

    def visit_while(self, node: "WhileNode") -> T:
        pass

    def visit_exprstmt(self, node: "ExpressionStatementNode") -> T:
        pass


class TraversalVisitor(Visitor[None]):
    """
    A basic visitor to traverse all the nodes in the AST.

    This is indended to be easily overridden, so as to more easily reach the
    nodes of interest.
    """

    def visit_spec(self, node: "SpecNode"):
        for chunk in node.chunks:
            chunk.accept(self)
        for block in node.blocks:
            block.accept(self)

    def visit_chunk(self, node: "ChunkNode"):
        for var in node.variables:
            var.accept(self)

    def visit_extern(self, node: "ExternChunkNode"):
        for var in node.variables:
            var.accept(self)

    def visit_block(self, node: "BlockNode"):
        for stmt in node.statements:
            stmt.accept(self)

    def visit_declaration(self, node: "DeclarationNode"):
        node.vartype.accept(self)

    def visit_special_declaration(self, node: "SpecialDeclarationNode"):
        pass

    def visit_type_simple(self, node: "SimpleTypeNode"):
        pass

    def visit_type_pointer(self, node: "PointerTypeNode"):
        node.base.accept(self)

    def visit_type_array(self, node: "ArrayTypeNode"):
        node.base.accept(self)

    def visit_type_func(self, node: "FuncTypeNode"):
        for arg in node.args:
            arg.accept(self)
        node.ret.accept(self)

    def visit_assignment(self, node: "AssignmentNode"):
        node.target.accept(self)
        node.expression.accept(self)

    def visit_ref(self, node: "RefNode"):
        node.target.accept(self)

    def visit_deref(self, node: "DerefNode"):
        node.target.accept(self)

    def visit_array(self, node: "ArrayNode"):
        node.target.accept(self)
        node.index.accept(self)

    def visit_binary(self, node: "BinaryOperationNode"):
        node.left.accept(self)
        node.right.accept(self)

    def visit_variable(self, node: "VariableNode"):
        pass

    def visit_function(self, node: "FunctionNode"):
        for arg in node.arguments:
            arg.accept(self)

    def visit_value(self, node: "ValueNode"):
        pass

    def visit_call(self, node: "CallNode"):
        pass

    def visit_split(self, node: "SplitNode"):
        pass

    def visit_if(self, node: "IfNode"):
        node.condition.accept(self)
        for statement in node.statements:
            statement.accept(self)

        if node.else_if:
            node.else_if.accept(self)
        if node.else_statements:
            for statement in node.else_statements:
                statement.accept(self)

    def visit_while(self, node: "WhileNode"):
        node.condition.accept(self)
        for statement in node.statements:
            statement.accept(self)

    def visit_exprstmt(self, node: "ExpressionStatementNode"):
        node.expression.accept(self)
