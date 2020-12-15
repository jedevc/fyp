import json
import os
import shlex
import subprocess
from glob import glob
from typing import List, Optional

from .tags import Tag


class Library:
    def __init__(self, name: str, path: str, includes: List[str]):
        self.name = name
        self.path = path
        self.includes = [
            f
            for include in includes
            for f in glob(os.path.join(path, include), recursive=True)
        ]

    def build(self):
        if os.path.exists(os.path.join(self.path, "configure")):
            run_cmd("./configure", cwd=self.path)
        if os.path.exists(os.path.join(self.path, "Makefile")):
            run_cmd("make -j", cwd=self.path)

    def tags(self):
        tags = []
        for include in self.includes:
            tags += ctags(include)
        return tags


def ctags(header_path: str):
    kinds = "+xp"
    fields = "+Sn"

    cmd = " ".join(
        [
            "ctags",
            "-f -",
            "--output-format=json",
            f"--kinds-c={kinds}",
            f"--fields={fields} {header_path}",
        ]
    )
    output = run_cmd(cmd, capture_output=True)
    if not output:
        return []

    lines = output.strip().split("\n")
    return [Tag(json.loads(line)) for line in lines]


def run_cmd(
    cmd: str, cwd: Optional[str] = None, capture_output: bool = False
) -> Optional[str]:
    print(f"$ {cmd}")
    cmd_words = shlex.split(cmd)

    stdout = subprocess.PIPE if capture_output else None
    proc = subprocess.run(cmd_words, cwd=cwd, stdout=stdout, check=True)
    if stdout:
        return proc.stdout.decode()
    else:
        return None
