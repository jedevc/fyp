import io
import subprocess
from pathlib import Path

import pytest

import synth


def xfailproc(args):
    return pytest.param(
        args, marks=pytest.mark.xfail(raises=subprocess.CalledProcessError)
    )


@pytest.mark.parametrize(
    "example",
    [
        xfailproc("protostar/stack/stack0.txt"),
        xfailproc("protostar/stack/stack1.txt"),
        xfailproc("protostar/stack/stack2.txt"),
        "protostar/stack/stack3.txt",
        "protostar/stack/stack4.txt",
        "protostar/stack/stack5.txt",
    ],
)
def test_synth(example):
    path = Path("examples") / example
    with open(path) as f:
        source_code = f.read()

    output = io.StringIO()
    synth.synthesize(source_code, output)
    c_code = output.getvalue()
    output.close()

    subprocess.run(
        ["gcc", "-x", "c", "-o", "/dev/null", "-"], input=c_code.encode(), check=True
    )
