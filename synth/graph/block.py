from typing import List, Optional, Union

from ..builtins import functions, variables
from ..node import Operator as OperatorType
from .chunk import Chunk

Lvalue = Union["Variable", "Array", "Deref"]
Expression = Union["Operation", "Function", "Value", "Ref", Lvalue]
Statement = Union["Assignment", "Call", "If", "While", "ExpressionStatement"]


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


class While:
    def __init__(self, condition: Expression, stmts: List[Statement]):
        self.condition = condition
        self.statements = stmts

    @property
    def code(self) -> str:
        block = "{\n" + "".join(stmt.code for stmt in self.statements) + "}"
        return f"while ({self.condition.code}) {block}\n"


class Function:
    def __init__(self, func: str, args: List[Expression]):
        self.func = func
        self.args = args

    @property
    def code(self) -> str:
        if self.func in functions.TRANSLATIONS:
            func = functions.TRANSLATIONS[self.func]
        else:
            func = self.func
        return f"{func}({', '.join(arg.code for arg in self.args)})"


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
    def __init__(self, variable: str, chunk: Optional[Chunk]):
        self.variable = variable
        self.chunk = chunk

    @property
    def code(self) -> str:
        if self.variable in variables.TRANSLATIONS:
            return variables.TRANSLATIONS[self.variable]
        else:
            return self.variable


class Value:
    def __init__(self, value: str):
        self.value = value

    @property
    def code(self) -> str:
        return self.value