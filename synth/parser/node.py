from typing import Any, List, Union

from .token import Token

Lvalue = Union["VariableNode", "ArrayNode", "DerefNode"]
Expression = Union["FunctionNode", "ValueNode", "RefNode", Lvalue]
Statement = Union["AssignmentNode", "CallNode", Expression]

Type = Union["SimpleTypeNode", "PointerTypeNode", "ArrayTypeNode", "FuncTypeNode"]


class Node:
    def __init__(self, start: Token, end: Token):
        self.token_start = start
        self.token_end = end

    def accept(self, visitor: "Visitor") -> Any:
        raise NotImplementedError()


class SimpleTypeNode(Node):
    def __init__(self, start: Token, end: Token, core: str):
        super().__init__(start, end)
        self.core = core

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_type_simple(self)


class PointerTypeNode(Node):
    def __init__(self, start: Token, end: Token, base: Type):
        super().__init__(start, end)
        self.base = base

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_type_pointer(self)


class ArrayTypeNode(Node):
    def __init__(self, start: Token, end: Token, base: Type, size: int):
        super().__init__(start, end)
        self.base = base
        self.size = size

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_type_array(self)


class FuncTypeNode(Node):
    def __init__(self, start: Token, end: Token, ret: Type, args: List[Type]):
        super().__init__(start, end)
        self.ret = ret
        self.args = args

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_type_func(self)


class DeclarationNode(Node):
    def __init__(self, start: Token, end: Token, name: str, vartype: Type):
        super().__init__(start, end)
        self.name = name
        self.vartype = vartype

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_declaration(self)


class SpecialDeclarationNode(Node):
    def __init__(self, start: Token, end: Token, name: str):
        super().__init__(start, end)
        self.name = name

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_special_declaration(self)


class ChunkNode(Node):
    def __init__(
        self,
        start: Token,
        end: Token,
        variables: List[Union[DeclarationNode, SpecialDeclarationNode]],
    ):
        super().__init__(start, end)
        self.variables = variables

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_chunk(self)


class ExternChunkNode(ChunkNode):
    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_extern(self)


class FunctionNode(Node):
    def __init__(
        self, start: Token, end: Token, target: str, arguments: List[Expression]
    ):
        super().__init__(start, end)
        self.target = target
        self.arguments = arguments

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_function(self)


class CallNode(Node):
    def __init__(self, start: Token, end: Token, target: str):
        super().__init__(start, end)
        self.target = target

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_call(self)


class RefNode(Node):
    def __init__(self, start: Token, end: Token, target: Lvalue):
        super().__init__(start, end)
        self.target = target

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_ref(self)


class DerefNode(Node):
    def __init__(self, start: Token, end: Token, target: Expression):
        super().__init__(start, end)
        self.target = target

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_deref(self)


class VariableNode(Node):
    def __init__(self, start: Token, end: Token, name: str):
        super().__init__(start, end)
        self.name = name

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_variable(self)


class ArrayNode(Node):
    def __init__(self, start: Token, end: Token, target: Expression, index: Expression):
        super().__init__(start, end)
        self.target = target
        self.index = index

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_array(self)


class ValueNode(Node):
    def __init__(self, start: Token, end: Token, value: Union[str, int]):
        super().__init__(start, end)
        self.value = value

    def is_str(self) -> bool:
        return isinstance(self.value, str)

    def is_int(self) -> bool:
        return isinstance(self.value, int)

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_value(self)


class AssignmentNode(Node):
    def __init__(
        self, start: Token, end: Token, target: Lvalue, expression: Expression
    ):
        super().__init__(start, end)
        self.target = target
        self.expression = expression

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_assignment(self)


class BlockNode(Node):
    def __init__(
        self, start: Token, end: Token, name: str, statements: List[Statement]
    ):
        super().__init__(start, end)
        self.name = name
        self.statements = statements

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_block(self)


class SpecNode(Node):
    def __init__(
        self, start: Token, end: Token, chunks: List[ChunkNode], blocks: List[BlockNode]
    ):
        super().__init__(start, end)
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
