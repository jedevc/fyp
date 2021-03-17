import sys
from pathlib import Path

import pytest

import vulnspec

from .helpers import FunctionGenerator

PROTOSTAR_HELPERS = [
    (FunctionGenerator.print, "flag", "FLAG{}"),
    (FunctionGenerator.exit, "tryagain", "Try again!"),
]


@pytest.mark.parametrize(
    ("example", "functions"),
    [
        ("protostar/stack/stack0.txt", PROTOSTAR_HELPERS),
        ("protostar/stack/stack1.txt", PROTOSTAR_HELPERS),
        ("protostar/stack/stack2.txt", PROTOSTAR_HELPERS),
        ("protostar/stack/stack3.txt", []),
        ("protostar/stack/stack4.txt", []),
        ("protostar/stack/stack5.txt", []),
    ],
)
def test_synth(example, functions, tmp_path):
    path = Path("examples") / example
    source_code = path.read_text()

    program = tmp_path / "program.c"
    helpers = tmp_path / "helpers.c"

    for _ in range(5):
        # Because the synthesis process is partly random, we repeat the
        # generation multiple times to try and ensure we acheive adequate
        # coverage.

        with program.open("w") as f:
            vulnspec.synthesize(
                source_code,
                f,
                dump={
                    vulnspec.DumpType.AST: sys.stderr,
                    vulnspec.DumpType.ASTDiagram: sys.stderr,
                    vulnspec.DumpType.GraphBlock: sys.stderr,
                    vulnspec.DumpType.GraphBlockChunk: sys.stderr,
                },
            )

        if functions:
            with helpers.open("w") as f:
                gen = FunctionGenerator()
                for args in functions:
                    func, args = args[0], args[1:]
                    func(gen, *args)
                gen.code(f)

        vulnspec.run_commands(program.read_text(), "build")
