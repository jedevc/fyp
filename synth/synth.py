import argparse
import subprocess
import sys
from typing import Optional, TextIO

from .assets import Asset
from .error import SynthError
from .graph.codegen import CodeGen
from .interpret import Interpreter


def main() -> Optional[int]:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("infile", type=argparse.FileType("r"))
    arg_parser.add_argument("outfile", type=argparse.FileType("w"))
    arg_parser.add_argument(
        "--print-ast", action="store_true", help="Dump the parsed AST"
    )
    arg_parser.add_argument(
        "--format",
        choices=["none", "llvm", "google", "chromium", "mozilla", "webkit"],
        default="webkit",
        help="Coding style to output",
    )
    args = arg_parser.parse_args()

    stream = args.infile.read()

    try:
        synthesize(stream, args.outfile, print_ast=args.print_ast, style=args.format)
    except SynthError as err:
        print(err.format(stream), file=sys.stderr)
        return 1

    return 0


def synthesize(
    stream: str, output: TextIO, style: str = "none", print_ast: bool = False
):
    asset = Asset.load(stream, print_ast=print_ast)

    inter = Interpreter(asset.blocks, asset.chunks, asset.extern)
    prog = inter.program()
    gen = CodeGen(prog)
    code = gen.generate()

    if style == "none":
        print(code, file=output)
    else:
        subprocess.run(
            ["clang-format", f"-style={style}"],
            input=code.encode(),
            stdout=output,
            check=True,
        )
