from typing import List, Union

from .chunk import Chunk
from .node import Operator as OperatorType

Lvalue = Union["Variable", "Array", "Deref"]
Expression = Union["Operation", "Function", "Value", "Ref", Lvalue]
Statement = Union["Assignment", "Call", "If", "ExpressionStatement"]


class ExpressionStatement:
    def __init__(self, expr: Expression):
        self.expr = expr

    @property
    def code(self) -> str:
        return self.expr.code + ";\n"


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
        lines = [stmt.code for stmt in self.statements]

        if self.func == "main":
            # NOTE: once we have function types, this will be much neater
            lines.append("return 0;\n")
            block = "{\n" + "".join(lines) + "}\n"
            return f"int main() {block}"
        else:
            block = "{\n" + "".join(lines) + "}\n"
            return f"void {self.func}() {block}"


class Assignment:
    def __init__(self, target: Lvalue, value: Expression):
        self.target = target
        self.value = value

    @property
    def code(self) -> str:
        return f"{self.target.code} = {self.value.code};\n"


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


class If:
    def __init__(
        self, condition: Expression, ifs: List[Statement], elses: List[Statement]
    ):
        self.condition = condition
        self.ifs = ifs
        self.elses = elses

    @property
    def code(self) -> str:
        if_block = "{\n" + "".join(stmt.code for stmt in self.ifs) + "}"
        else_block = "{\n" + "".join(stmt.code for stmt in self.elses) + "}"

        if self.elses:
            return f"if ({self.condition.code}) {if_block} else {else_block}\n"
        else:
            return f"if ({self.condition.code}) {if_block}\n"


class Function:
    def __init__(self, func: str, args: List[Expression]):
        self.func = func
        self.args = args

    @property
    def code(self) -> str:
        return f"{self.func}({', '.join(arg.code for arg in self.args)})"


class Operation:
    def __init__(self, op: OperatorType, left: Expression, right: Expression):
        self.op = op
        self.left = left
        self.right = right

    @property
    def code(self) -> str:
        op = {
            OperatorType.Add: "+",
            OperatorType.Subtract: "-",
            OperatorType.Multiply: "*",
            OperatorType.Divide: "/",
            OperatorType.Eq: "==",
            OperatorType.Neq: "!=",
            OperatorType.Gt: ">",
            OperatorType.Gte: ">=",
            OperatorType.Lt: "<",
            OperatorType.Lte: "<=",
        }[self.op]
        return f"({self.left.code} {op} {self.right.code})"


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
