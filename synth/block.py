from typing import List, Union

from .chunk import Chunk

Expression = Union["Function", "Variable"]
Statement = Union["Assignment", "Call", Expression]


class Block:
    def __init__(self):
        self.statements = []
        self.functions = []

    def add_statement(self, statement: Statement):
        self.statements.append(statement)

    def add_function(self, function: "FunctionDefinition"):
        self.functions.append(function)

    @property
    def code(self) -> str:
        parts = []
        parts += [func.code for func in self.functions]
        # TODO: we shouldn't allow statements encoded here to be translated to code
        parts += [stmt.code + ";" for stmt in self.statements]
        return "\n".join(parts)


class FunctionDefinition:
    def __init__(self, func: str, args: List[str]):
        self.func = func
        self.args = args
        self.statements: List[Statement] = []

    def add_statement(self, statement: Statement):
        self.statements.append(statement)

    @property
    def code(self) -> str:
        lines = [f"\t{stmt};" for stmt in self.statements]
        block = "{\n" + "\n".join(lines) + "\n}"
        return f"void {self.func}() {block}"


class Assignment:
    def __init__(self, chunk: Chunk, variable: str, value: Expression):
        self.chunk = chunk
        if (var := chunk.lookup(variable)) :
            self.variable = var
        else:
            raise KeyError()

        self.value = value

    @property
    def code(self) -> str:
        return f"{self.variable} = {self.value.code}"


class Call:
    def __init__(self, block: Block):
        self.block = block

    @property
    def code(self) -> str:
        raise RuntimeError("calls cannot be translated directly into code")


class Function:
    def __init__(self, func: str, args: List[Expression]):
        self.func = func
        self.args = args

    @property
    def code(self) -> str:
        return f"{self.func}({', '.join(arg.code for arg in self.args)})"


class Variable:
    def __init__(self, chunk: Chunk, variable: str, address: bool):
        self.chunk = chunk
        self.variable = variable
        self.address = address

    @property
    def code(self) -> str:
        if self.address:
            return "&" + self.variable
        else:
            return self.variable


class Value:
    def __init__(self, value: Union[str, int]):
        self.value = value

    @property
    def code(self) -> str:
        if isinstance(self.value, str):
            return '"' + self.value + '"'
        elif isinstance(self.value, int):
            return str(self.value)
        else:
            raise RuntimeError("value is of invalid type")
