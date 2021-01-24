from typing import TYPE_CHECKING, Generic, Optional, TypeVar

if TYPE_CHECKING:
    from .base import Node
    from .expr import (
        ArrayNode,
        BinaryOperationNode,
        DerefNode,
        FunctionNode,
        LiteralNode,
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
    from .types import (
        ArrayTypeNode,
        FuncTypeNode,
        PointerTypeNode,
        SimpleTypeNode,
        UnknownTypeNode,
    )

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

    def visit_type_unknown(self, node: "UnknownTypeNode") -> T:
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

    def visit_literal(self, node: "LiteralNode") -> T:
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


class TraversalVisitor(Visitor[Optional[T]]):
    """
    A basic visitor to traverse all the nodes in the AST.

    This is indended to be easily overridden, so as to more easily reach the
    nodes of interest.
    """

    def visit_spec(self, node: "SpecNode") -> Optional[T]:
        for chunk in node.chunks:
            chunk.accept(self)
        for block in node.blocks:
            block.accept(self)

        return None

    def visit_chunk(self, node: "ChunkNode") -> Optional[T]:
        for var in node.variables:
            var.accept(self)

        return None

    def visit_extern(self, node: "ExternChunkNode") -> Optional[T]:
        for var in node.variables:
            var.accept(self)

        return None

    def visit_block(self, node: "BlockNode") -> Optional[T]:
        for stmt in node.statements:
            stmt.accept(self)

        return None

    def visit_declaration(self, node: "DeclarationNode") -> Optional[T]:
        node.vartype.accept(self)

        return None

    def visit_special_declaration(self, node: "SpecialDeclarationNode") -> Optional[T]:
        return None

    def visit_type_unknown(self, node: "UnknownTypeNode") -> Optional[T]:
        return None

    def visit_type_simple(self, node: "SimpleTypeNode") -> Optional[T]:
        return None

    def visit_type_pointer(self, node: "PointerTypeNode") -> Optional[T]:
        node.base.accept(self)

        return None

    def visit_type_array(self, node: "ArrayTypeNode") -> Optional[T]:
        node.base.accept(self)

        return None

    def visit_type_func(self, node: "FuncTypeNode") -> Optional[T]:
        for arg in node.args:
            arg.accept(self)
        node.ret.accept(self)

        return None

    def visit_assignment(self, node: "AssignmentNode") -> Optional[T]:
        node.target.accept(self)
        node.expression.accept(self)

        return None

    def visit_ref(self, node: "RefNode") -> Optional[T]:
        node.target.accept(self)

        return None

    def visit_deref(self, node: "DerefNode") -> Optional[T]:
        node.target.accept(self)

        return None

    def visit_array(self, node: "ArrayNode") -> Optional[T]:
        node.target.accept(self)
        node.index.accept(self)

        return None

    def visit_binary(self, node: "BinaryOperationNode") -> Optional[T]:
        node.left.accept(self)
        node.right.accept(self)

        return None

    def visit_variable(self, node: "VariableNode") -> Optional[T]:
        return None

    def visit_function(self, node: "FunctionNode") -> Optional[T]:
        node.target.accept(self)
        for arg in node.arguments:
            arg.accept(self)

        return None

    def visit_value(self, node: "ValueNode") -> Optional[T]:
        return None

    def visit_call(self, node: "CallNode") -> Optional[T]:
        return None

    def visit_split(self, node: "SplitNode") -> Optional[T]:
        return None

    def visit_if(self, node: "IfNode") -> Optional[T]:
        node.condition.accept(self)
        for statement in node.statements:
            statement.accept(self)

        if node.else_if:
            node.else_if.accept(self)
        if node.else_statements:
            for statement in node.else_statements:
                statement.accept(self)

        return None

    def visit_while(self, node: "WhileNode") -> Optional[T]:
        node.condition.accept(self)
        for statement in node.statements:
            statement.accept(self)

        return None

    def visit_exprstmt(self, node: "ExpressionStatementNode") -> Optional[T]:
        node.expression.accept(self)

        return None
