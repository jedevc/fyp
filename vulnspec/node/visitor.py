from typing import TYPE_CHECKING, Any, Generic, Optional, TypeVar

if TYPE_CHECKING:
    from .base import Node
    from .expr import (
        ArrayNode,
        BinaryOperationNode,
        CastNode,
        DerefNode,
        FunctionNode,
        LiteralExpressionNode,
        RefNode,
        SizeOfNode,
        UnaryOperationNode,
        ValueNode,
        VariableNode,
    )
    from .high import BlockNode, ChunkNode, DeclarationNode, ExternChunkNode, SpecNode
    from .stmt import (
        AssignmentNode,
        CallNode,
        ExpressionStatementNode,
        IfNode,
        LiteralStatementNode,
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

    def visit_literal_expr(self, node: "LiteralExpressionNode") -> T:
        pass

    def visit_literal_stmt(self, node: "LiteralStatementNode") -> T:
        pass

    def visit_cast(self, node: "CastNode") -> T:
        pass

    def visit_variable(self, node: "VariableNode") -> T:
        pass

    def visit_ref(self, node: "RefNode") -> T:
        pass

    def visit_deref(self, node: "DerefNode") -> T:
        pass

    def visit_array(self, node: "ArrayNode") -> T:
        pass

    def visit_unary(self, node: "UnaryOperationNode") -> T:
        pass

    def visit_binary(self, node: "BinaryOperationNode") -> T:
        pass

    def visit_function(self, node: "FunctionNode") -> T:
        pass

    def visit_value(self, node: "ValueNode") -> T:
        pass

    def visit_sizeof(self, node: "SizeOfNode") -> T:
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
        if node.initial:
            node.initial.accept(self)

        return None

    def visit_type_simple(self, node: "SimpleTypeNode") -> Optional[T]:
        return None

    def visit_type_pointer(self, node: "PointerTypeNode") -> Optional[T]:
        node.base.accept(self)

        return None

    def visit_type_array(self, node: "ArrayTypeNode") -> Optional[T]:
        node.base.accept(self)
        if node.size:
            node.size.accept(self)

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

    def visit_literal_expr(self, node: "LiteralExpressionNode") -> Optional[T]:
        return None

    def visit_literal_stmt(self, node: "LiteralStatementNode") -> Optional[T]:
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

    def visit_unary(self, node: "UnaryOperationNode") -> Optional[T]:
        node.item.accept(self)

        return None

    def visit_binary(self, node: "BinaryOperationNode") -> Optional[T]:
        node.left.accept(self)
        node.right.accept(self)

        return None

    def visit_cast(self, node: "CastNode") -> Optional[T]:
        node.cast.accept(self)
        node.expr.accept(self)

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

    def visit_sizeof(self, node: "SizeOfNode") -> Optional[T]:
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


class MapVisitor(Visitor[Any]):
    def visit_spec(self, node: "SpecNode") -> "SpecNode":
        for i, chunk in enumerate(node.chunks):
            node.chunks[i] = chunk.accept(self)
        for i, block in enumerate(node.blocks):
            node.blocks[i] = block.accept(self)

        return node

    def visit_chunk(self, node: "ChunkNode") -> "ChunkNode":
        for i, var in enumerate(node.variables):
            node.variables[i] = var.accept(self)

        return node

    def visit_extern(self, node: "ExternChunkNode") -> "ExternChunkNode":
        for i, var in enumerate(node.variables):
            node.variables[i] = var.accept(self)

        return node

    def visit_block(self, node: "BlockNode") -> "BlockNode":
        for i, stmt in enumerate(node.statements):
            node.statements[i] = stmt.accept(self)

        return node

    def visit_declaration(self, node: "DeclarationNode") -> "DeclarationNode":
        node.vartype = node.vartype.accept(self)
        if node.initial:
            node.initial = node.initial.accept(self)

        return node

    def visit_type_simple(self, node: "SimpleTypeNode") -> "SimpleTypeNode":
        return node

    def visit_type_pointer(self, node: "PointerTypeNode") -> "PointerTypeNode":
        node.base = node.base.accept(self)
        return node

    def visit_type_array(self, node: "ArrayTypeNode") -> "ArrayTypeNode":
        node.base = node.base.accept(self)
        if node.size:
            node.size = node.size.accept(self)
        return node

    def visit_type_func(self, node: "FuncTypeNode") -> "FuncTypeNode":
        for i, arg in enumerate(node.args):
            node.args[i] = arg.accept(self)
        node.ret = node.ret.accept(self)

        return node

    def visit_assignment(self, node: "AssignmentNode") -> "AssignmentNode":
        node.target = node.target.accept(self)
        node.expression = node.expression.accept(self)

        return node

    def visit_literal_expr(
        self, node: "LiteralExpressionNode"
    ) -> "LiteralExpressionNode":
        return node

    def visit_literal_stmt(
        self, node: "LiteralStatementNode"
    ) -> "LiteralStatementNode":
        return node

    def visit_ref(self, node: "RefNode") -> "RefNode":
        node.target = node.target.accept(self)

        return node

    def visit_deref(self, node: "DerefNode") -> "DerefNode":
        node.target = node.target.accept(self)

        return node

    def visit_array(self, node: "ArrayNode") -> "ArrayNode":
        node.target = node.target.accept(self)
        node.index = node.index.accept(self)

        return node

    def visit_unary(self, node: "UnaryOperationNode") -> "UnaryOperationNode":
        node.item = node.item.accept(self)

        return node

    def visit_binary(self, node: "BinaryOperationNode") -> "BinaryOperationNode":
        node.left = node.left.accept(self)
        node.right = node.right.accept(self)

        return node

    def visit_cast(self, node: "CastNode") -> "CastNode":
        node.cast = node.cast.accept(self)
        node.expr = node.expr.accept(self)

        return node

    def visit_variable(self, node: "VariableNode") -> "VariableNode":
        return node

    def visit_function(self, node: "FunctionNode") -> "FunctionNode":
        node.target = node.target.accept(self)
        for i, arg in enumerate(node.arguments):
            node.arguments[i] = arg.accept(self)

        return node

    def visit_value(self, node: "ValueNode") -> "ValueNode":
        return node

    def visit_sizeof(self, node: "SizeOfNode") -> "SizeOfNode":
        return node

    def visit_call(self, node: "CallNode") -> "CallNode":
        return node

    def visit_split(self, node: "SplitNode") -> "SplitNode":
        return node

    def visit_if(self, node: "IfNode") -> "IfNode":
        node.condition = node.condition.accept(self)
        for i, statement in enumerate(node.statements):
            node.statements[i] = statement.accept(self)

        if node.else_if:
            node.else_if = node.else_if.accept(self)
        if node.else_statements:
            for i, statement in enumerate(node.else_statements):
                node.else_statements[i] = statement.accept(self)

        return node

    def visit_while(self, node: "WhileNode") -> "WhileNode":
        node.condition = node.condition.accept(self)
        for i, statement in enumerate(node.statements):
            node.statements[i] = statement.accept(self)

        return node

    def visit_exprstmt(
        self, node: "ExpressionStatementNode"
    ) -> "ExpressionStatementNode":
        node.expression = node.expression.accept(self)

        return node
