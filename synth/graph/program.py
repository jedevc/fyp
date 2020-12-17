from .block import FunctionDefinition
from .chunk import ChunkVariable


class Program:
    def __init__(self):
        self.globals = []
        self.externs = []

        self.functions = []

    def add_global(self, var: ChunkVariable):
        self.globals.append(var)

    def add_extern(self, var: ChunkVariable):
        self.externs.append(var)

    def add_function(self, func: FunctionDefinition):
        self.functions.append(func)

    @property
    def code(self) -> str:
        parts = []
        parts += [f"{var.code};" for var in self.globals]
        parts += [f"extern {var.code};" for var in self.externs]
        parts += [func.code for func in self.functions]
        return "\n".join(parts)
