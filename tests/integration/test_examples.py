import io
import subprocess
from pathlib import Path

import pytest

import synth

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
        ("protostar/stack/stack3.txt", PROTOSTAR_HELPERS),
        ("protostar/stack/stack4.txt", PROTOSTAR_HELPERS),
        ("protostar/stack/stack5.txt", PROTOSTAR_HELPERS),
    ],
)
def test_synth(example, functions):
    path = Path("examples") / example
    with open(path) as f:
        source_code = f.read()

    output = io.StringIO()
    synth.synthesize(source_code, output)
    program_code = output.getvalue()
    output.close()

    gen = FunctionGenerator()
    for args in functions:
        func, args = args[0], args[1:]
        func(gen, *args)
    helper_code = gen.code()

    subprocess.run(
        ["gcc", "-c", "-x", "c", "-o", "/tmp/one.o", "-"],
        input=helper_code.encode(),
        check=True,
    )
    subprocess.run(
        ["gcc", "-c", "-x", "c", "-o", "/tmp/two.o", "-"],
        input=program_code.encode(),
        check=True,
    )
    subprocess.run(["gcc", "/tmp/one.o", "/tmp/two.o", "-o", "/dev/null"], check=True)
