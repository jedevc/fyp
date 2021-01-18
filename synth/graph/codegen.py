from typing import List, Set

from ..builtins import functions, types, variables
from .block import (
    Array,
    Assignment,
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
        parts.extend(f"extern {self._gen_decl(var)};" for var in program.externs)
        parts.append("")
        parts.extend(f"{self._gen_decl(var)};" for var in program.globals)
        parts.append("")
        parts.extend(self._gen_func_decl(func) for func in program.functions)

        includes = [f"#include <{include}>" for include in self._includes]

        return "\n".join(includes + [""] + parts)

    def _gen_decl(self, var: ChunkVariable) -> str:
        for tp in var.basic_types():
            try:
                ttp = types.TRANSLATIONS[tp]
                self._includes.add(types.PATHS[ttp])
            except KeyError:
                pass

        return var.typename()

    def _gen_func_decl(self, func: FunctionDefinition) -> str:
        lines = [self._gen_stmt(stmt) for stmt in func.statements]

        if func.func == "main":
            # NOTE: once we have function types, this will be much neater
            lines.append("return 0;\n")
            block = "{\n" + "".join(lines) + "}\n"
            return f"int main(int argc, char *argv[]) {block}"
        else:
            block = "{\n" + "".join(lines) + "}\n"
            return f"void {func.func}() {block}"

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
            lines.append("}\n")
            return "".join(lines)
        elif isinstance(stmt, While):
            block = (
                "{\n" + "".join(self._gen_stmt(stmt) for stmt in stmt.statements) + "}"
            )
            return f"while ({self._gen_expr(stmt.condition)}) {block}\n"
        elif isinstance(stmt, ExpressionStatement):
            return self._gen_expr(stmt.expr) + ";\n"
        else:
            raise RuntimeError("cannot be translated into code")

    def _gen_expr(self, expr: Expression) -> str:
        if isinstance(expr, Variable):
            if expr.variable in variables.TRANSLATIONS:
                vname = variables.TRANSLATIONS[expr.variable]
                self._includes.add(variables.PATHS[vname])
            else:
                vname = expr.variable
            return vname
        elif isinstance(expr, Function):
            if expr.func in functions.TRANSLATIONS:
                fname = functions.TRANSLATIONS[expr.func]
                self._includes.add(functions.PATHS[fname])
            else:
                fname = expr.func
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
            }[expr.op]
            return (
                "(" + self._gen_expr(expr.left) + op + self._gen_expr(expr.right) + ")"
            )
        elif isinstance(expr, Value):
            return expr.value
        elif isinstance(expr, Deref):
            return "*" + self._gen_expr(expr.target)
        elif isinstance(expr, Ref):
            return "&" + self._gen_expr(expr.target)
        else:
            raise RuntimeError("cannot be translated into code")
