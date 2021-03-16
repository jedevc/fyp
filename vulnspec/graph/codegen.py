from typing import List, Optional, Set

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
            parts.extend(
                f"extern {self._gen_decl(var)};" for var in program.externs.values()
            )
            parts.append("")
        if program.globals:
            parts.extend(f"{self._gen_decl(var)};" for var in program.globals.values())
            parts.append("")

        for func in program.functions.values():
            decl = self._gen_func_decl(func)
            if decl is not None:
                parts.append(decl)
        for func in program.functions.values():
            defi = self._gen_func_def(func)
            parts.append(defi)

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

    def _gen_func_decl(self, func: FunctionDefinition) -> Optional[str]:
        if func.func == "main":
            return None

        if func.args:
            args = ", ".join(self._gen_decl(arg) for arg in func.args)
        else:
            args = ""
        return f"void {func.func}({args});"

    def _gen_func_def(self, func: FunctionDefinition) -> str:
        lines: List[str] = []
        if func.statics:
            lines.extend(f"static {self._gen_decl(var)};" for var in func.statics)
        if func.locals:
            lines.extend(f"{self._gen_decl(var)};" for var in func.locals)
        lines.extend(self._gen_stmt(stmt) for stmt in func.statements)

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
                    lines.append(
                        f"if {self._gen_expr(condition, force_parens=True)}" + " {\n"
                    )
                    lines.extend([self._gen_stmt(stmt) for stmt in statements])
                elif condition is None:
                    lines.append("} else {\n")
                    lines.extend([self._gen_stmt(stmt) for stmt in statements])
                else:
                    cond = self._gen_expr(condition, force_parens=True)
                    lines.append("} " + f"else if {cond}" + " {\n")
                    lines.extend([self._gen_stmt(stmt) for stmt in statements])
            lines.append("}")
            return "".join(lines)
        elif isinstance(stmt, While):
            block = (
                "{\n" + "".join(self._gen_stmt(stmt) for stmt in stmt.statements) + "}"
            )
            return f"while {self._gen_expr(stmt.condition, force_parens=True)} {block}"
        elif isinstance(stmt, ExpressionStatement):
            return self._gen_expr(stmt.expr) + ";\n"
        elif isinstance(stmt, StatementGroup):
            return "".join(self._gen_stmt(stmt) for stmt in stmt.statements)
        else:
            raise RuntimeError("cannot be translated into code")

    def _gen_expr(self, expr: Expression, force_parens: bool = False) -> str:
        result: str
        if isinstance(expr, Variable):
            if expr.variable.name in variables.TRANSLATIONS:
                vname = variables.TRANSLATIONS[expr.variable.name]
                self._includes.add(variables.PATHS[vname])
            elif expr.variable.name in functions.TRANSLATIONS:
                vname = functions.TRANSLATIONS[expr.variable.name]
                self._includes.add(functions.PATHS[vname])
            else:
                vname = expr.variable.name
            result = vname
        elif isinstance(expr, Function):
            fname = self._gen_expr(expr.func)
            result = f"{fname}({', '.join(self._gen_expr(arg) for arg in expr.args)})"
        elif isinstance(expr, Array):
            result = f"{self._gen_expr(expr.target)}[{self._gen_expr(expr.index)}]"
        elif isinstance(expr, Operation):
            op = expr.op.opstr()
            if len(expr.operands) == 1:
                result = op + self._gen_expr(expr.operands[0])
            elif len(expr.operands) == 2:
                left, right = expr.operands
                result = self._gen_expr(left) + op + self._gen_expr(right)
            else:
                raise RuntimeError()

            if not force_parens:
                # only wrap with parens when we're not going to do it later
                result = f"({result})"
        elif isinstance(expr, Value):
            if expr.value in ("false", "true"):
                self._includes.add("stdbool.h")

            result = expr.value
        elif isinstance(expr, Cast):
            # FIXME: this is a bit hacky
            typestr = ChunkVariable("", expr.cast, None).typestr()
            result = f"({typestr}) {self._gen_expr(expr.expr)}"
        elif isinstance(expr, Deref):
            result = "*" + self._gen_expr(expr.target)
        elif isinstance(expr, Ref):
            result = "&" + self._gen_expr(expr.target)
        else:
            raise RuntimeError("cannot be translated into code")

        if force_parens:
            result = f"({result})"

        return result
