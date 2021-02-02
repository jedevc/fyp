import subprocess

import pytest


class FunctionGenerator:
    def __init__(self):
        self.libraries = set()
        self.functions = []

    def code(self) -> str:
        if not self.functions:
            return ""

        includes = "\n".join(f"#include <{include}>" for include in self.libraries)
        definitions = "\n\n".join(self.functions)

        return includes + "\n\n" + definitions

    def print(self, funcname: str, message: str):
        self.libraries.add("stdio.h")

        block = self._block(f'puts("{message}")')
        func = f"void {funcname}() {block}"
        self.functions.append(func)

    def exit(self, funcname: str, message: str = ""):
        self.libraries.add("stdlib.h")

        if message:
            block = self._block(f'puts("{message}")', "exit(1)")
            self.libraries.add("stdio.h")
        else:
            block = self._block("exit(1)")
        func = f"void {funcname}() {block}"
        self.functions.append(func)

    def _block(self, *stmts: str) -> str:
        inner = "".join(f"\t{stmt};\n" for stmt in stmts)
        return "{\n" + inner + "}"


def xfailproc(*args):
    return pytest.param(
        *args, marks=pytest.mark.xfail(raises=subprocess.CalledProcessError)
    )
