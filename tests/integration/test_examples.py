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
    stream = path.read_text()

    program = tmp_path / "program.c"
    helpers = tmp_path / "helpers.c"
    helpers.symlink_to(path.parent.resolve() / "helpers.c")

    config = vulnspec.Configuration(program, stream)

    for _ in range(5):
        # Because the synthesis process is partly random, we repeat the
        # generation multiple times to try and ensure we acheive adequate
        # coverage.

        _, gen_program = vulnspec.synthesize(
            stream,
            dump={
                vulnspec.DumpType.AST: sys.stderr,
                vulnspec.DumpType.ASTDiagram: sys.stderr,
                vulnspec.DumpType.GraphBlock: sys.stderr,
                vulnspec.DumpType.GraphBlockChunk: sys.stderr,
            },
        )
        code = vulnspec.gen_code(gen_program, config, file_comment=True, style="webkit")
        program.write_text(code)

        vulnspec.run_commands(program.read_text(), "build")
