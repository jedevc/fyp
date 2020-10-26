from typing import List, Optional


class Node:
    def __init__(self):
        pass

    def visit(self, visitor: "Visitor"):
        raise NotImplementedError()


class VariableNode:
    def __init__(self, name: str, vartype: str):
        super().__init__()
        self.name = name
        self.vartype = vartype

    def visit(self, visitor: "Visitor"):
        visitor.visit_variable(self)


class ChunkNode:
    def __init__(self, variables: List[VariableNode]):
        super().__init__()
        self.variables = variables
        self._variable_map = {node.name: node for node in variables}

    def lookup(self, name: str) -> Optional[VariableNode]:
        return self._variable_map.get(name)

    def visit(self, visitor: "Visitor"):
        visitor.visit_chunk(self)
        for var in self.variables:
            var.visit(visitor)


class SpecNode:
    def __init__(self, chunks: List[ChunkNode]):
        super().__init__()
        self.chunks = chunks

    def lookup(self, name: str) -> Optional[VariableNode]:
        for chunk in self.chunks:
            var = chunk.lookup(name)
            if var is not None:
                return var
        return None

    def visit(self, visitor: "Visitor"):
        visitor.visit_spec(self)
        for chunk in self.chunks:
            chunk.visit(visitor)


class Visitor:
    def __init__(self):
        pass

    def visit_chunk(self, node: ChunkNode):
        pass

    def visit_variable(self, node: VariableNode):
        pass

    def visit_spec(self, node: SpecNode):
        pass
