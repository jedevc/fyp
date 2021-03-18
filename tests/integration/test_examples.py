import sys
from pathlib import Path

import pytest

import vulnspec


@pytest.mark.parametrize(
    "example",
    [
        "protostar/stack/stack0.txt",
        "protostar/stack/stack1.txt",
        "protostar/stack/stack2.txt",
        "protostar/stack/stack3.txt",
        "protostar/stack/stack4.txt",
        "protostar/stack/stack5.txt",
    ],
)
def test_synth(example, tmp_path):
    path = Path("examples") / example
    source_code = path.read_text()

    program = tmp_path / "program.c"

    helpers = tmp_path / "helpers.c"
    helpers.symlink_to(path.parent.resolve() / "helpers.c")

    for _ in range(5):
        # Because the synthesis process is partly random, we repeat the
        # generation multiple times to try and ensure we acheive adequate
        # coverage.

        with program.open("w") as f:
            vulnspec.synthesize(
                source_code,
                f,
                vulnspec.Configuration(source_code),
                dump={
                    vulnspec.DumpType.AST: sys.stderr,
                    vulnspec.DumpType.ASTDiagram: sys.stderr,
                    vulnspec.DumpType.GraphBlock: sys.stderr,
                    vulnspec.DumpType.GraphBlockChunk: sys.stderr,
                },
            )

        vulnspec.run_commands(program.read_text(), "build")
