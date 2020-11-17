from typing import Any, List, Union

from .token import Token

Expression = Union["FunctionNode", "VariableNode", "ValueNode"]
Statement = Union["AssignmentNode", "CallNode", Expression]


class Node:
    def __init__(self, start: Token, end: Token):
        self.token_start = start
        self.token_end = end

    def accept(self, visitor: "Visitor") -> Any:
        raise NotImplementedError()


class TypeNode(Node):
    def __init__(self, start: Token, end: Token, base: str, size: int = 1):
        super().__init__(start, end)
        self.base = base
        self.size = size

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_type(self)


class DeclarationNode(Node):
    def __init__(self, start: Token, end: Token, name: str, vartype: TypeNode):
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


class GlobalChunkNode(ChunkNode):
    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_global(self)


class FunctionNode(Node):
    def __init__(
        self, start: Token, end: Token, name: str, arguments: List[Expression]
    ):
        super().__init__(start, end)
        self.name = name
        self.arguments = arguments

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_function(self)


class CallNode(Node):
    def __init__(self, start: Token, end: Token, target: str):
        super().__init__(start, end)
        self.target = target

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_call(self)


class VariableNode(Node):
    def __init__(self, start: Token, end: Token, target: str, address: bool = False):
        super().__init__(start, end)
        self.target = target
        self.address = address

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_variable(self)


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
    def __init__(self, start: Token, end: Token, name: str, expression: Expression):
        super().__init__(start, end)
        self.name = name
        self.expression = expression

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_assignment(self)


class BlockNode(Node):
    def __init__(
        self, start: Token, end: Token, label: str, statements: List[Statement]
    ):
        super().__init__(start, end)
        self.label = label
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

    def visit_chunk(self, node: ChunkNode) -> Any:
        pass

    def visit_global(self, node: GlobalChunkNode) -> Any:
        pass

    def visit_block(self, node: BlockNode) -> Any:
        pass

    def visit_assignment(self, node: AssignmentNode) -> Any:
        pass

    def visit_variable(self, node: VariableNode) -> Any:
        pass

    def visit_function(self, node: FunctionNode) -> Any:
        pass

    def visit_value(self, node: ValueNode) -> Any:
        pass

    def visit_call(self, node: CallNode) -> Any:
        pass

    def visit_type(self, node: TypeNode) -> Any:
        pass

    def visit_declaration(self, node: DeclarationNode) -> Any:
        pass

    def visit_special_declaration(self, node: SpecialDeclarationNode) -> Any:
        pass

    def visit_spec(self, node: SpecNode) -> Any:
        pass
