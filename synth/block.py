from typing import List, Union

from .chunk import Chunk

Lvalue = Union["Variable", "Deref"]
Expression = Union["Function", "Value", "Ref", Lvalue]
Statement = Union["Assignment", "Call", Expression]


class Block:
    def __init__(self, name: str):
        self.name = name
        self.statements: List[Statement] = []

    def add_statement(self, statement: Statement):
        self.statements.append(statement)


class FunctionDefinition:
    def __init__(self, func: str, args: List[str]):
        self.func = func
        self.args = args
        self.statements: List[Statement] = []

    def add_statement(self, statement: Statement):
        self.statements.append(statement)

    @property
    def code(self) -> str:
        lines = [f"\t{stmt.code};" for stmt in self.statements]

        if self.func == "main":
            # NOTE: once we have function types, this will be much neater
            lines.append("\treturn 0;")
            block = "{\n" + "\n".join(lines) + "\n}"
            return f"int main() {block}"
        else:
            block = "{\n" + "\n".join(lines) + "\n}"
            return f"void {self.func}() {block}"


class Assignment:
    def __init__(self, target: Lvalue, value: Expression):
        self.target = target
        self.value = value

    @property
    def code(self) -> str:
        return f"{self.target.code} = {self.value.code}"


class Deref:
    def __init__(self, target: Lvalue):
        self.target = target

    @property
    def code(self) -> str:
        return f"*{self.target.code}"


class Ref:
    def __init__(self, target: Lvalue):
        self.target = target

    @property
    def code(self) -> str:
        return f"&{self.target.code}"


class Array:
    def __init__(self, target: Lvalue, index: Expression):
        self.target = target
        self.index = index

    @property
    def code(self) -> str:
        return f"{self.target.code}[{self.index.code}]"


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
    def __init__(self, chunk: Chunk, variable: str):
        self.chunk = chunk
        self.variable = variable

    @property
    def code(self) -> str:
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
