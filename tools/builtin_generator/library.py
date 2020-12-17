import json
import shlex
import subprocess
from pathlib import Path
from typing import List, Optional

from .tags import Tag


class Library:
    def __init__(self, name: str, path: Path, includes: List[str]):
        self.name = name
        self.path = path
        self.includes = includes

    def build(self):
        if (self.path / "configure").exists():
            run_cmd("./configure", cwd=self.path)
        if (self.path / "Makefile").exists():
            run_cmd("make -j", cwd=self.path)

    def tags(self):
        tags = []
        for include in self.includes:
            include_dir = self.path / include
            for header in include_dir.glob("**/*.h"):
                relative = str(header).removeprefix(str(include_dir)).strip("/")
                tags += ctags(include_dir, Path(relative))
        return tags


def ctags(base: Path, header: Path):
    kinds = "+xp"
    fields = "+Sn"

    cmd = " ".join(
        [
            "ctags",
            "-f -",
            "--output-format=json",
            f"--kinds-c={kinds}",
            f"--fields={fields} {header}",
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
    print(f"$ {cmd}")
    cmd_words = shlex.split(cmd)

    stdout = subprocess.PIPE if capture_output else None
    proc = subprocess.run(cmd_words, cwd=cwd, stdout=stdout, check=True)
    if stdout:
        return proc.stdout.decode()
    else:
        return None
