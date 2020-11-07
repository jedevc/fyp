from typing import Any, List, Union


class Node:
    def __init__(self):
        pass

    def accept(self, visitor: "Visitor") -> Any:
        raise NotImplementedError()


class TypeNode(Node):
    def __init__(self, base: str, size: int = 1):
        super().__init__()
        self.base = base
        self.size = size

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_type(self)


class DeclarationNode(Node):
    def __init__(self, name: str, vartype: TypeNode):
        super().__init__()
        self.name = name
        self.vartype = vartype

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_variable(self)


class SpecialDeclarationNode(Node):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_special_variable(self)


class ChunkNode(Node):
    def __init__(self, variables: List[Union[DeclarationNode, SpecialDeclarationNode]]):
        super().__init__()
        self.variables = variables

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_chunk(self)


class SpecNode(Node):
    def __init__(self, chunks: List[ChunkNode]):
        super().__init__()
        self.chunks = chunks

    def accept(self, visitor: "Visitor") -> Any:
        return visitor.visit_spec(self)


class Visitor:
    def __init__(self):
        pass

    def visit_chunk(self, node: ChunkNode) -> Any:
        pass

    def visit_type(self, node: TypeNode) -> Any:
        pass

    def visit_variable(self, node: DeclarationNode) -> Any:
        pass

    def visit_special_variable(self, node: SpecialDeclarationNode) -> Any:
        pass

    def visit_spec(self, node: SpecNode) -> Any:
        pass
