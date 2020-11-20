from typing import List

from .block import Block, Call, Function, FunctionDefinition
from .chunk import ChunkSet, Variable


class Program:
    def __init__(self):
        self.globals = []
        self.functions = []

    def add_global(self, var: Variable):
        self.globals.append(var)

    def add_function(self, func: FunctionDefinition):
        self.functions.append(func)

    @property
    def code(self) -> str:
        parts = []
        parts += [f"{var.code};" for var in self.globals]
        parts += [func.code for func in self.functions]
        return "\n".join(parts)


class Interpreter:
    def __init__(self, blocks: List[Block], chunks: ChunkSet):
        self.blocks = blocks
        self.chunks = chunks

    def program(self) -> Program:
        final = Program()

        for block in self.blocks:
            func = FunctionDefinition(block.name, [])
            for stmt in block.statements:
                if isinstance(stmt, Call):
                    new_stmt = Function(stmt.block.name, [])
                    func.add_statement(new_stmt)
                else:
                    func.add_statement(stmt)

            final.add_function(func)

        for var in self.chunks.variables:
            final.add_global(var)

        return final
