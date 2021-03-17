import subprocess
from typing import TextIO

import pytest


class FunctionGenerator:
    def __init__(self):
        self.libraries = set()
        self.functions = []

    def code(self, output: TextIO):
        if not self.functions:
            return

        for lib in self.libraries:
            print(f"#include <{lib}>", file=output)
        print()
        for func in self.functions:
            print(func, file=output)

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
