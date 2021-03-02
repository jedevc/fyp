import argparse
import random
import subprocess
import sys
from functools import reduce
from typing import Optional, TextIO

from .assets import Asset, AssetLoader
from .error import SynthError
from .graph import merge_chunks
from .graph.codegen import CodeGen
from .interpret import Interpreter
from .nops import NopTransformer


def main() -> Optional[int]:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("infile", type=argparse.FileType("r"))
    arg_parser.add_argument("outfile", type=argparse.FileType("w"))
    arg_parser.add_argument("--seed", help="Random seed to use")
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
        synthesize(
            stream, args.outfile, args.seed, print_ast=args.print_ast, style=args.format
        )
    except SynthError as err:
        print(err, file=sys.stderr)
        return 1

    return 0


def synthesize(
    stream: str,
    output: TextIO,
    seed: Optional[str] = None,
    style: str = "none",
    print_ast: bool = False,
):
    if seed is not None:
        random.seed(seed)

    asset = Asset.load(stream, print_ast=print_ast)

    nops = AssetLoader.list("nops", external=True)
    noper = NopTransformer(nops)
    blocks = [noper.transform(block) for block in asset.blocks] + list(
        noper.additional_blocks
    )
    chunks = asset.chunks + list(noper.additional_chunks)
    extern = reduce(merge_chunks, [asset.extern, *noper.additional_externs])

    inter = Interpreter(blocks, chunks, extern)
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
