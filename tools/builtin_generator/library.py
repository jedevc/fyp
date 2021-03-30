import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, TextIO, Union

from .tags import Tag


class Library:
    def __init__(self, name: str, path: Path, subpaths: List[str]):
        self.name = name
        self.path = path
        self.subpaths = subpaths

        if not self.path.exists():
            raise FileNotFoundError(f"library {self.name} does not exist")

    def build(self):
        if (self.path / "configure").exists():
            run_cmd("./configure", cwd=self.path)
        if (self.path / "Makefile").exists():
            run_cmd("make -j", cwd=self.path)

    def tags(
        self,
        headers: bool = True,
        sources: bool = False,
        extra_flags: Optional[List[str]] = None,
    ):
        tags = []
        for p in self.subpaths:
            subpath = self.path / p

            if headers:
                for header in subpath.glob("**/*.h"):
                    relative = header.relative_to(subpath)
                    tags += ctags(subpath, Path(relative), extra_flags)
            if sources:
                for header in subpath.glob("**/*.c"):
                    relative = header.relative_to(subpath)
                    tags += ctags(subpath, Path(relative), extra_flags)
        return tags


def ctags(base: Path, header: Path, extra_flags: Optional[List[str]] = None):
    kinds = "+xp"
    fields = "+Sn"

    extra_flags = extra_flags or []

    cmd = " ".join(
        [
            "ctags",
            "-f -",
            "--output-format=json",
            f"--kinds-c={kinds}",
            f"--fields={fields}",
            *extra_flags,
            str(header),
        ]
    )
    output = run_cmd(cmd, cwd=base, capture_output=True)
    if not output:
        return []

    lines = output.strip().split("\n")
    return [Tag(json.loads(line)) for line in lines]


def run_cmd(
    cmd: str, cwd: Optional[Path] = None, capture_output: bool = False
) -> Optional[str]:
    print(f"$ {cmd}", file=sys.stderr)
    cmd_words = shlex.split(cmd)

    stdout: Union[int, TextIO]
    if capture_output:
        stdout = subprocess.PIPE
    else:
        stdout = sys.stderr

    proc = subprocess.run(cmd_words, cwd=cwd, stdout=stdout, check=True)
    if proc.stdout:
        return proc.stdout.decode()
    else:
        return None
