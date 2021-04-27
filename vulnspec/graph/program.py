from typing import Dict, Set

from .block import FunctionDefinition
from .chunk import ChunkVariable


class Program:
    def __init__(self):
        self.includes: Set[str] = set()

        self.globals: Dict[str, ChunkVariable] = {}
        self.externs: Dict[str, ChunkVariable] = {}

        self.functions: Dict[str, FunctionDefinition] = {}

    def add_global(self, var: ChunkVariable):
        self.globals[var.name] = var

    def add_extern(self, var: ChunkVariable):
        self.externs[var.name] = var

    def add_function(self, func: FunctionDefinition):
        self.functions[func.func] = func

    def add_include(self, include: str):
        self.includes.add(include)
