import os
import subprocess
from pathlib import Path

import pytest

import vulnspec

FLAG = "FLAG{}"


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
    solvefile = tmp_path / "solve.py"
    flagfile = tmp_path / "flag.txt"

    helpers.symlink_to(path.parent.resolve() / "helpers.c")
    flagfile.write_text(FLAG + "\n")

    config = vulnspec.Configuration(program, stream)

    devnull = open(os.devnull, "w")

    for _ in range(5):
        # Because the synthesis process is partly random, we repeat the
        # generation multiple times to try and ensure we acheive adequate
        # coverage.

        # synthesize program
        gen_asset, gen_program = vulnspec.synthesize(
            stream,
            dump={
                vulnspec.DumpType.AST: devnull,
                vulnspec.DumpType.ASTDiagram: devnull,
                vulnspec.DumpType.GraphBlock: devnull,
                vulnspec.DumpType.GraphBlockChunk: devnull,
            },
        )
        code = vulnspec.gen_code(gen_program, config, file_comment=True, style="webkit")
        program.write_text(code)
        vulnspec.run_commands(program.read_text(), "build")

        # generate solution
        solve = vulnspec.gen_solve(
            path.with_suffix(".solve.py").read_text(), gen_asset.attachments, config
        )
        solvefile.write_text(solve)

        # attempt solution
        cmd = ["python", str(solvefile)]
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=tmp_path,
            check=True,
            timeout=2,
        )
        assert FLAG in proc.stdout.decode()

    devnull.close()
