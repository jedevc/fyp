import subprocess
from pathlib import Path
from typing import Dict

from vulnspec import Configuration, gen_code, gen_solve, synthesize

challenge_root = Path("/tmp/ctf")


class Challenge:
    _source_cache: Dict[Path, str] = {}

    def __init__(
        self, source: Path, output: Path, seed: str, force_recreate: bool = False
    ):
        self.source = source
        if source in Challenge._source_cache:
            self.stream = Challenge._source_cache[source]
        else:
            self.stream = source.read_text()
            Challenge._source_cache[source] = self.stream

        self.output = output
        if self.output.exists() and not force_recreate:
            return
        self.output.mkdir(parents=True)

        # synthesize
        asset, program = synthesize(self.stream, seed)
        config = Configuration(self.c, self.stream)
        code = gen_code(program, config, style="webkit")
        self.c.write_text(code)

        # build
        for command in config.build_commands():
            subprocess.run(command, cwd=output, shell=True, check=True)
        assert self.binary.exists()

        # solve (optional)
        if (solve := self.source.with_suffix(".solve.py")).exists():
            solve_script = solve.read_text()
            solve_script = gen_solve(solve_script, asset.attachments, config)
            self.solve.write_text(solve_script)

    @property
    def c(self) -> Path:
        return self.output / "challenge.c"

    @property
    def binary(self) -> Path:
        return self.output / "challenge"

    @property
    def solve(self) -> Path:
        return self.output / "solve.py"

    @staticmethod
    def create(source: Path, seed: str) -> "Challenge":
        return Challenge(
            source, challenge_root / source.with_suffix("").name / seed, seed
        )
