import io
from pathlib import Path

import pytest

import synth

from .helpers import FunctionGenerator, Toolchain

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
        ("protostar/stack/stack3.txt", PROTOSTAR_HELPERS),
        ("protostar/stack/stack4.txt", PROTOSTAR_HELPERS),
        ("protostar/stack/stack5.txt", PROTOSTAR_HELPERS),
    ],
)
def test_synth(example, functions, tmp_path):
    path = Path("examples") / example
    with open(path) as f:
        source_code = f.read()

    for _ in range(5):
        # Because the synthesis process is partly random, we repeat the
        # generation multiple times to try and ensure we acheive adequate
        # coverage.

        output = io.StringIO()
        synth.synthesize(source_code, output, print_ast=True, visualize_ast=True)
        program_code = output.getvalue()
        output.close()

        gen = FunctionGenerator()
        for args in functions:
            func, args = args[0], args[1:]
            func(gen, *args)
        helper_code = gen.code()

        helper_path = tmp_path / "helpers.o"
        program_path = tmp_path / "program.o"

        Toolchain.compile(helper_path, helper_code)
        Toolchain.compile(program_path, program_code)
        Toolchain.link(Path("/dev/null"), helper_path, program_path)
