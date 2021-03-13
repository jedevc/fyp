import configparser
from pathlib import Path
from typing import Iterable, List


class CompilerConfig:
    COMPILER_DEFAULTS = {
        "cc": "gcc",
        "warnings": "no",
        "strip": "no",
        "debug": "no",
    }

    SECURITY_DEFAULTS = {
        "relro": "no",
        "canary": "no",
        "nx": "no",
        "pie": "no",
    }

    def __init__(self, source: str):
        self.config = configparser.ConfigParser()
        self.config["compile"] = CompilerConfig.COMPILER_DEFAULTS
        self.config["security"] = CompilerConfig.SECURITY_DEFAULTS
        for comment in _extract_comments(source):
            if comment.startswith("[compile]\n"):
                self.config.read_string(comment)
            elif comment.startswith("[security]\n"):
                self.config.read_string(comment)

    def commands(self, source: Path) -> List[str]:
        sources = [str(source)]

        output = str(source.with_suffix(""))

        command = [self.cc, *self.cflags, *sources, "-o", output]
        return [" ".join(command)]

    @property
    def cc(self) -> str:
        return self.config["compile"]["cc"]

    @property
    def cflags(self) -> List[str]:
        flags: List[str] = []

        # assorted flags
        if self.config["compile"].getboolean("strip"):
            flags.append("-s")
        if self.config["compile"].getboolean("debug"):
            flags.append("-g")

        # warnings
        flags.extend(
            {
                "no": [""],
                "all": ["-Wall"],
                "extra": ["-Wall", "-Wextra"],
            }[self.config["compile"]["warnings"]]
        )

        # f-flags
        if self.config["security"].getboolean("canary"):
            flags.append("-fstack-protector-all")
        else:
            flags.append("-fno-stack-protector")

        if self.config["security"].getboolean("pie"):
            flags.append("-fPIC")
            flags.append("-pie")
        else:
            flags.append("-no-pie")

        # linking
        if self.config["security"].getboolean("nx"):
            flags.extend(["-z", "noexecstack"])
        else:
            flags.extend(["-z", "execstack"])

        flags.extend(
            {
                "no": ["-z", "norelro"],
                "partial": ["-z", "relro"],
                "full": ["-z", "relro", "-z", "now"],
            }[self.config["security"]["relro"]]
        )

        return list(filter(None, flags))


def _extract_comments(stream: str) -> Iterable[str]:
    comment = ""
    while stream:
        if stream.startswith("//"):
            stream = stream[2:].lstrip()
            if (n := stream.find("\n")) != -1:
                comment += stream[: n + 1]
                stream = stream[n + 1 :]
            else:
                comment += stream
                stream = ""
        else:
            if comment:
                yield comment.strip()
                comment = ""

            if stream.startswith("/*"):
                stream = stream[2:].lstrip()
                while not stream.startswith("*/"):
                    comment += stream[0]
                    stream = stream[1:]

                yield comment.strip()
                comment = ""
            else:
                stream = stream[1:]

    if comment:
        yield comment.strip()
