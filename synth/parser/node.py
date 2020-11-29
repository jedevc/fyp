from typing import Any, List, Union

Lvalue = Union["VariableNode", "ArrayNode", "DerefNode"]
Expression = Union["FunctionNode", "ValueNode", "RefNode", Lvalue]
Statement = Union["AssignmentNode", "CallNode", "IfNode", "ExpressionStatementNode"]

Type = Union["SimpleTypeNode", "PointerTypeNode", "ArrayTypeNode", "FuncTypeNode"]


class Node:
    def __init__(self):
        self.token_start = None
        self.token_end = None

    def accept(self, visitor: "Visitor") -> Any:
        raise NotImplementedError()


class SimpleTypeNode(Node):
    def __init__(self, core: str):
        super().__init__()
        self.core = core

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_type_simple(self)


class PointerTypeNode(Node):
    def __init__(self, base: Type):
        super().__init__()
        self.base = base

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_type_pointer(self)


class ArrayTypeNode(Node):
    def __init__(self, base: Type, size: int):
        super().__init__()
        self.base = base
        self.size = size

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_type_array(self)


class FuncTypeNode(Node):
    def __init__(self, ret: Type, args: List[Type]):
        super().__init__()
        self.ret = ret
        self.args = args

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_type_func(self)


class DeclarationNode(Node):
    def __init__(self, name: str, vartype: Type):
        super().__init__()
        self.name = name
        self.vartype = vartype

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_declaration(self)


class SpecialDeclarationNode(Node):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_special_declaration(self)


class ChunkNode(Node):
    def __init__(self, variables: List[Union[DeclarationNode, SpecialDeclarationNode]]):
        super().__init__()
        self.variables = variables

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_chunk(self)


class ExternChunkNode(ChunkNode):
    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_extern(self)


class FunctionNode(Node):
    def __init__(self, target: str, arguments: List[Expression]):
        super().__init__()
        self.target = target
        self.arguments = arguments

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_function(self)


class CallNode(Node):
    def __init__(self, target: str):
        super().__init__()
        self.target = target

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_call(self)


class RefNode(Node):
    def __init__(self, target: Lvalue):
        super().__init__()
        self.target = target

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_ref(self)


class DerefNode(Node):
    def __init__(self, target: Expression):
        super().__init__()
        self.target = target

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_deref(self)


class VariableNode(Node):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_variable(self)


class ArrayNode(Node):
    def __init__(self, target: Expression, index: Expression):
        super().__init__()
        self.target = target
        self.index = index

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_array(self)


class ValueNode(Node):
    def __init__(self, value: Union[str, int]):
        super().__init__()
        self.value = value

    def is_str(self) -> bool:
        return isinstance(self.value, str)

    def is_int(self) -> bool:
        return isinstance(self.value, int)

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_value(self)


class AssignmentNode(Node):
    def __init__(self, target: Lvalue, expression: Expression):
        super().__init__()
        self.target = target
        self.expression = expression

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_assignment(self)


class IfNode(Node):
    def __init__(self, condition: Expression, statements: List[Statement]):
        super().__init__()
        self.condition = condition
        self.statements = statements

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_if(self)


class ExpressionStatementNode(Node):
    def __init__(self, expression: Expression):
        super().__init__()
        self.expression = expression

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_exprstmt(self)


class BlockNode(Node):
    def __init__(self, name: str, statements: List[Statement]):
        super().__init__()
        self.name = name
        self.statements = statements

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_block(self)


class SpecNode(Node):
    def __init__(self, chunks: List[ChunkNode], blocks: List[BlockNode]):
        super().__init__()
        self.chunks = chunks
        self.blocks = blocks

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_spec(self)


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
