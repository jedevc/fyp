import json
import os
import re
import shlex
import subprocess
import sys

from .tags import Tag


def prepare():
    cwd = os.path.basename(os.getcwd())
    if re.match(r"musl-\d+\.\d+\.\d+", cwd) is None:
        print("error: not currently in a libmusl directory", file=sys.stderr)
        sys.exit(1)

    run_cmd("./configure")
    run_cmd("make -j")


def ctags(path: str):
    kinds = "+xp"
    fields = "+Sn"

    cmd = " ".join(
        [
            "ctags",
            "-f -",
            "--output-format=json",
            f"--kinds-c={kinds}",
            f"--fields={fields} {path}",
        ]
    )
    output = run_cmd(cmd, capture_output=True)
    if not output:
        return []

    lines = output.strip().split("\n")
    return [Tag(json.loads(line)) for line in lines]


def run_cmd(cmd: str, capture_output=False):
    print(f"$ {cmd}")
    cmd_words = shlex.split(cmd)
    if capture_output:
        proc = subprocess.run(cmd_words, check=True, stdout=subprocess.PIPE)
        return proc.stdout.decode()
    else:
        subprocess.run(cmd_words, check=True)
        print()
        return None
