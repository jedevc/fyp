import json
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Set, TextIO, Union

from .tags import Tag


class Library:
    def __init__(
        self, name: str, root: Path, includes: List[str], include_locations: List[str]
    ):
        self.name = name
        self.root = root
        self.includes = includes
        self.include_locations = include_locations

        if not self.root.exists():
            raise FileNotFoundError(f"library {self.name} does not exist")

    def build(self):
        if (self.root / "configure").exists():
            run_cmd("./configure", cwd=self.root)
        if (self.root / "Makefile").exists():
            run_cmd("make -j", cwd=self.root)

    def tags(
        self,
        headers: bool = True,
        sources: bool = False,
        extra_flags: Optional[List[str]] = None,
    ) -> List[Tag]:
        tags = []

        for prefix in self.includes:
            path = self.root / prefix

            locations = []
            if sources:
                locations += list(path.glob("**/*.c"))
            if headers:
                locations += list(path.glob("**/*.h"))

            for loc in locations:
                ntags = self._tags(loc, extra_flags)
                for tag in ntags:
                    tag.path = str(loc.relative_to(path))
                tags += ntags

        return tags

    def _tags(
        self,
        include: Path,
        extra_flags: Optional[List[str]] = None,
        exclude: Optional[Set[Path]] = None,
    ) -> List[Tag]:
        if exclude is None:
            exclude = set()
        exclude.add(include)

        tags = ctags(include, extra_flags)

        contents = include.read_text()
        matches = re.finditer('^#include [<"](.+)[>"]$', contents, flags=re.MULTILINE)
        for match in matches:
            target = match.group(1)
            for loc in self.include_locations:
                path = self.root / loc / target
                if path in exclude:
                    continue

                if path.exists():
                    tags += self._tags(path, extra_flags, exclude=exclude)
                    break

        return tags


def ctags(header: Path, extra_flags: Optional[List[str]] = None):
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
    output = run_cmd(cmd, capture_output=True)
    if not output:
        return []

    lines = output.strip().split("\n")
    return [Tag(json.loads(line)) for line in lines]


def run_cmd(
    cmd: str, cwd: Optional[Path] = None, capture_output: bool = False
) -> Optional[str]:
    # print(f"$ {cmd}", file=sys.stderr)
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
