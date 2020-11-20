from typing import List

from .block import Block, Call, Function, FunctionDefinition
from .chunk import ChunkSet


class Interpreter:
    def __init__(self, blocks: List[Block], chunks: ChunkSet):
        self.blocks = blocks
        self.chunks = chunks

    def block(self) -> Block:
        final = Block("")

        for block in self.blocks:
            func = FunctionDefinition(block.name, [])
            for stmt in block.statements:
                if isinstance(stmt, Call):
                    new_stmt = Function(stmt.block.name, [])
                    func.add_statement(new_stmt)
                else:
                    func.add_statement(stmt)

            final.add_function(func)

        return final
