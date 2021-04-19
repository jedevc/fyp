import configparser
import io
import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional

GENERIC_FLAGS = [
    "-fno-zero-initialized-in-bss",
]


class Configuration:
    COMPILER_DEFAULTS = {
        "cc": "gcc",
        "arch": "default",
        "warnings": "no",
        "strip": "no",
        "debug": "no",
        "debug_separate": "no",
    }

    SECURITY_DEFAULTS = {
        "relro": "no",
        "canary": "no",
        "nx": "no",
        "pie": "no",
    }

    ENVIRONMENT_DEFAULTS = {
        "type": "raw-raw-raw",
        "port": "",
        "script": "",
    }

    def __init__(self, source_path: Path, spec: str):
        # if source_path.suffix != ".c":
        #     raise ValueError("output path must be a C file")

        self.source_path = source_path
        self.dest_path = source_path.with_suffix("")
        self.spec = spec

        self.config = configparser.ConfigParser(allow_no_value=True)
        self.config["compile"] = Configuration.COMPILER_DEFAULTS
        self.config["security"] = Configuration.SECURITY_DEFAULTS
        self.config["files"] = {}
        self.config["env"] = Configuration.ENVIRONMENT_DEFAULTS
        for comment in _extract_comments(self.spec):
            if comment.startswith("[compile]\n"):
                self.config.read_string(comment)
            elif comment.startswith("[security]\n"):
                self.config.read_string(comment)
            elif comment.startswith("[files]\n"):
                self.config.read_string(comment)
            elif comment.startswith("[env]\n"):
                self.config.read_string(comment)

    @property
    def debug_path(self) -> Optional[Path]:
        if self.config["compile"].getboolean("debug_separate"):
            return self.dest_path.with_suffix(".debug")
        else:
            return None

    def build_commands(
        self, relative: bool = False, absolute: bool = False
    ) -> List[str]:
        assert not (relative and absolute)

        def translate_path(p: Path) -> str:
            if relative:
                return p.name
            elif absolute:
                return str(p.absolute())
            else:
                return str(p)

        sources = [translate_path(self.source_path)]
        sources.extend(
            translate_path(self.source_path.parent / key)
            for key in self.config["files"].keys()
        )

        command = " ".join(
            [self.cc, *self.cflags, *sources, "-o", translate_path(self.dest_path)]
        )
        if self.debug_path:
            stripper = " ".join(
                [
                    "eu-strip",
                    "-g",
                    "-f",
                    translate_path(self.debug_path),
                    translate_path(self.dest_path),
                ]
            )
            return [command, stripper]
        else:
            return [command]

    @property
    def cc(self) -> str:
        if (cc := os.getenv("CC")) :
            return cc
        else:
            return self.config["compile"]["cc"]

    @property
    def cflags(self) -> List[str]:
        flags: List[str] = []

        # generic flags
        flags.extend(GENERIC_FLAGS)

        # architecture
        if self.config["compile"]["arch"] != "default":
            flags.append("-m" + self.config["compile"]["arch"])
            flags.append("-maccumulate-outgoing-args")

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

    @property
    def environ(self) -> "Environment":
        env = self.config["env"]
        access, interface, method = env["type"].split("-")
        return Environment(
            access,
            interface,
            method,
            int(env["port"]) if env["port"] else 4000,
            Path(env["script"]) if env["script"] else None,
        )


class Environment:
    USER = "pwn"
    DIRECTORY = Path(f"/home/{USER}")

    def __init__(
        self,
        access: str,
        interface: str,
        method: str,
        port: int = 4000,
        script: Optional[Path] = None,
    ):
        assert access in ("raw", "tcp", "ssh")
        assert interface in ("raw", "shell")
        assert method in ("raw", "basic", "setuid")

        self.access = access
        self.interface = interface
        self.method = method

        self.port = port
        self.script = script

    def docker(self, target: Path, extras: Dict[Path, Path]) -> str:
        output = io.StringIO()

        print("FROM ubuntu:latest", file=output)
        print(file=output)

        print("ARG user=pwn", file=output)
        if self.method != "raw":
            print("ARG flag", file=output)
        print(file=output)

        dependencies = []
        if self.method == "raw":
            pass
        elif self.access == "tcp":
            dependencies.append("ncat")
        elif self.access == "ssh":
            dependencies.append("openssh-server")

        print("RUN apt-get update && apt-get upgrade -y", file=output)
        print(f"RUN apt-get install -y {' '.join(dependencies)}", file=output)
        print(file=output)

        print("RUN chmod 3773 /tmp", file=output)
        print(file=output)

        targetdest = Environment.DIRECTORY / target

        print(f"COPY {target} {targetdest}", file=output)
        for extra_src, extra_dst in extras.items():
            print(f"COPY {extra_src} {Environment.DIRECTORY / extra_dst}", file=output)
        print(file=output)

        flagdest = Environment.DIRECTORY / "flag.txt"
        if self.method == "raw":
            pass
        elif self.method == "basic":
            print(f'RUN echo "$flag" > {flagdest}', file=output)
            print(file=output)
        elif self.method == "setuid":
            commands = [
                "useradd -ms /sbin/nologin owner",
                f'echo "$flag" > {flagdest}',
                f"chown -R owner:owner {Environment.DIRECTORY} {flagdest}",
                f"chmod u+s {targetdest}",
                f"chmod 600 {flagdest}",
            ]
            print(f"RUN {self.join_commands(commands)}", file=output)
            print(file=output)

        if self.script:
            print(f"COPY {self.script} /tmp/provision", file=output)
            print("RUN /tmp/provision && rm /tmp/provision", file=output)
            print(file=output)

        shell = "/bin/bash"

        if self.interface == "raw":
            binary = str(targetdest)
        elif self.interface == "shell":
            binary = shell

        if self.access == "raw":
            cmd = binary
        elif self.access == "tcp":
            cmd = f'ncat -lkp {self.port} -c "{binary}"'
        elif self.access == "ssh":
            shell = binary
            cmd = f"/usr/sbin/sshd -D -p {self.port}"

        print(f"RUN useradd -ms {shell} $user", file=output)

        if self.access == "ssh":
            commands = [
                "mkdir -p /run/sshd",
                "passwd -d $user",
                "echo 'PermitEmptyPasswords yes' >> /etc/ssh/sshd_config.d/empty-passwords.conf",
            ]
            print(f"RUN {self.join_commands(commands)}", file=output)
        else:
            print("USER $user", file=output)
            print(file=output)

        print(f"WORKDIR {Environment.DIRECTORY}", file=output)

        if self.port:
            print(f"EXPOSE {self.port}", file=output)
        print(f"CMD {cmd}", file=output)

        return output.getvalue()

    def join_commands(self, commands: List[str]) -> str:
        TAB = 4 * " "
        return f" && \\ \n{TAB}".join(commands)


def _extract_comments(stream: str) -> Iterable[str]:
    comment = ""
    while stream:
        if stream.startswith("//"):
            stream = stream[2:].lstrip(" ")
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
