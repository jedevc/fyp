import configparser
from pathlib import Path
from typing import Iterable, List, Optional, TextIO


class Configuration:
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

    ENVIRONMENT_DEFAULTS = {
        "type": "raw-raw-raw",
        "port": "1337",
        "script": "",
    }

    def __init__(self, source: str):
        self.config = configparser.ConfigParser(allow_no_value=True)
        self.config["compile"] = Configuration.COMPILER_DEFAULTS
        self.config["security"] = Configuration.SECURITY_DEFAULTS
        self.config["files"] = {}
        self.config["environment"] = Configuration.ENVIRONMENT_DEFAULTS
        for comment in _extract_comments(source):
            if comment.startswith("[compile]\n"):
                self.config.read_string(comment)
            elif comment.startswith("[security]\n"):
                self.config.read_string(comment)
            elif comment.startswith("[files]\n"):
                self.config.read_string(comment)
            elif comment.startswith("[environment]\n"):
                self.config.read_string(comment)

    def build_commands(self, source: Path) -> List[str]:
        sources = [str(source)]
        sources.extend(str(source.parent / key) for key in self.config["files"].keys())

        output = str(self.build_output(source))

        command = [self.cc, *self.cflags, *sources, "-o", output]
        return [" ".join(command)]

    def build_output(self, source: Path) -> Path:
        return source.with_suffix("")

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

    @property
    def environ(self) -> "Environment":
        env = self.config["environment"]
        access, interface, method = env["type"].split("-")
        return Environment(
            access,
            interface,
            method,
            int(env["port"]),
            Path(env["script"]) if env["script"] else None,
        )


class Environment:
    def __init__(
        self,
        access: str,
        interface: str,
        method: str,
        port: int,
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

    def docker(self, target: Path, output: TextIO):
        print("FROM ubuntu:latest", file=output)
        print("ARG flag", file=output)
        print("ARG user=pwn", file=output)

        dependencies = []
        if self.access == "tcp":
            dependencies.append("ncat")
        elif self.access == "ssh":
            dependencies.append("openssh-server")

        print("RUN apt-get update && apt-get upgrade -y", file=output)
        print(f"RUN apt-get install -y {' '.join(dependencies)}", file=output)

        print("RUN chmod 3773 /tmp", file=output)

        print(f"COPY {target.name} /opt/pwn/{target.name}", file=output)

        if self.method == "raw":
            pass
        elif self.method == "basic":
            print("RUN echo '$flag' > /flag.txt", file=output)
        elif self.method == "setuid":
            commands = [
                "useradd -ms /sbin/nologin owner",
                'echo "$flag" > /flag.txt',
                f"chown owner:owner /opt/pwn/{target.name} /flag.txt",
                f"chmod u+s /opt/pwn/{target.name}",
                "chmod 600 /flag.txt",
            ]
            cmdstr = " && \\ \n    ".join(commands)
            print(f"RUN {cmdstr}", file=output)

        if self.script:
            print(f"COPY {self.script} /tmp/provision", file=output)
            print("RUN /tmp/provision && rm /tmp/provision", file=output)

        shell = "/bin/bash"

        if self.interface == "raw":
            binary = f"/opt/pwn/{target.name}"
        elif self.interface == "shell":
            binary = shell

        if self.access == "raw":
            cmd = binary
        elif self.access == "tcp":
            cmd = f'ncat -lkp {self.port} -c "{binary}"'
        elif self.access == "ssh":
            shell = binary
            cmd = "sshd -D"

        print(f"RUN useradd -ms {shell} $user", file=output)
        print("USER $user", file=output)

        print(f"EXPOSE {self.port}", file=output)
        print(f"CMD {cmd}", file=output)


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
