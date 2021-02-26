from typing import List, Set

from ..builtins import functions, types, variables
from .block import (
    Array,
    Assignment,
    Cast,
    Deref,
    Expression,
    ExpressionStatement,
    Function,
    FunctionDefinition,
    If,
    Operation,
    OperatorType,
    Ref,
    Statement,
    StatementGroup,
    Value,
    Variable,
    While,
)
from .chunk import ChunkVariable
from .program import Program


class CodeGen:
    def __init__(self, program: Program):
        self.program = program

        self._includes: Set[str] = set()

    def generate(self) -> str:
        return self._gen_program(self.program)

    def _gen_program(self, program: Program) -> str:
        parts: List[str] = []
        if program.externs:
            parts.extend(f"extern {self._gen_decl(var)};" for var in program.externs)
            parts.append("")
        if program.globals:
            parts.extend(f"{self._gen_decl(var)};" for var in program.globals)
            parts.append("")

        parts.extend(self._gen_func_decl(func) for func in program.functions)

        if self._includes:
            includes = [f"#include <{include}>" for include in self._includes]
            parts = includes + [""] + parts

        return "\n".join(parts)

    def _gen_decl(self, var: ChunkVariable) -> str:
        for tp in var.basic_types():
            try:
                ttp = types.TRANSLATIONS[tp]
                self._includes.add(types.PATHS[ttp])
            except KeyError:
                pass

        if var.initial:
            return f"{var.typename()} = {self._gen_expr(var.initial)}"
        else:
            return var.typename()

    def _gen_func_decl(self, func: FunctionDefinition) -> str:
        lines = [self._gen_stmt(stmt) for stmt in func.statements]
        if func.locals is not None:
            lines = [f"{self._gen_decl(var)};" for var in func.locals.variables] + lines

        if func.func == "main":
            lines.append("return 0;\n")
            block = "{\n" + "".join(lines) + "}\n"
            return f"int main(int argc, char *argv[]) {block}"
        else:
            if func.args:
                args = ", ".join(self._gen_decl(arg) for arg in func.args)
            else:
                args = ""
            block = "{\n" + "".join(lines) + "}\n"
            return f"void {func.func}({args}) {block}"

    def _gen_stmt(self, stmt: Statement) -> str:
        if isinstance(stmt, Assignment):
            return f"{self._gen_expr(stmt.target)} = {self._gen_expr(stmt.value)};\n"
        elif isinstance(stmt, If):
            lines = []
            for i, (condition, statements) in enumerate(stmt.groups):
                if i == 0:
                    assert condition is not None
                    lines.append(f"if ({self._gen_expr(condition)})" + " {\n")
                    lines.extend([self._gen_stmt(stmt) for stmt in statements])
                elif condition is None:
                    lines.append("} else {\n")
                    lines.extend([self._gen_stmt(stmt) for stmt in statements])
                else:
                    lines.append(
                        "} " + f"else if ({self._gen_expr(condition)})" + " {\n"
                    )
                    lines.extend([self._gen_stmt(stmt) for stmt in statements])
            lines.append("}")
            return "".join(lines)
        elif isinstance(stmt, While):
            block = (
                "{\n" + "".join(self._gen_stmt(stmt) for stmt in stmt.statements) + "}"
            )
            return f"while ({self._gen_expr(stmt.condition)}) {block}"
        elif isinstance(stmt, ExpressionStatement):
            return self._gen_expr(stmt.expr) + ";\n"
        elif isinstance(stmt, StatementGroup):
            return "".join(self._gen_stmt(stmt) for stmt in stmt.statements)
        else:
            raise RuntimeError("cannot be translated into code")

    def _gen_expr(self, expr: Expression) -> str:
        if isinstance(expr, Variable):
            if expr.variable.name in variables.TRANSLATIONS:
                vname = variables.TRANSLATIONS[expr.variable.name]
                self._includes.add(variables.PATHS[vname])
            elif expr.variable.name in functions.TRANSLATIONS:
                vname = functions.TRANSLATIONS[expr.variable.name]
                self._includes.add(functions.PATHS[vname])
            else:
                vname = expr.variable.name
            return vname
        elif isinstance(expr, Function):
            fname = self._gen_expr(expr.func)
            return f"{fname}({', '.join(self._gen_expr(arg) for arg in expr.args)})"
        elif isinstance(expr, Array):
            return f"{self._gen_expr(expr.target)}[{self._gen_expr(expr.index)}]"
        elif isinstance(expr, Operation):
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
                OperatorType.And: "&&",
                OperatorType.Or: "||",
            }[expr.op]
            return (
                "(" + self._gen_expr(expr.left) + op + self._gen_expr(expr.right) + ")"
            )
        elif isinstance(expr, Value):
            if expr.value in ("false", "true"):
                self._includes.add("stdbool.h")

            return expr.value
        elif isinstance(expr, Cast):
            # FIXME: this is a bit hacky
            typestr = ChunkVariable("", expr.cast, None).typestr()
            return f"({typestr}) {self._gen_expr(expr.expr)}"
        elif isinstance(expr, Deref):
            return "*" + self._gen_expr(expr.target)
        elif isinstance(expr, Ref):
            return "&" + self._gen_expr(expr.target)
        else:
            raise RuntimeError("cannot be translated into code")
