import argparse
import random
import subprocess
import sys
from functools import reduce
from typing import Dict, Optional, TextIO

from .assets import Asset, AssetLoader
from .dump import DumpType
from .error import SynthError
from .graph import GraphVisualizer, merge_chunks
from .graph.codegen import CodeGen
from .interpret import Interpreter
from .nops import NopTransformer


def main() -> Optional[int]:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("infile", type=argparse.FileType("r"))
    arg_parser.add_argument("outfile", type=argparse.FileType("w"))
    arg_parser.add_argument("--seed", help="Random seed to use")
    arg_parser.add_argument(
        "--dump-ast", type=argparse.FileType("w"), help="Dump the parsed AST"
    )
    arg_parser.add_argument(
        "--dump-ast-diagram",
        type=argparse.FileType("w"),
        help="Dump a diagram of the parsed AST",
    )
    arg_parser.add_argument(
        "--dump-block-graph",
        type=argparse.FileType("w"),
        help="Dump the block graph",
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
            stream,
            args.outfile,
            args.seed,
            style=args.format,
            dump={
                DumpType.AST: args.dump_ast,
                DumpType.ASTDiagram: args.dump_ast_diagram,
                DumpType.GraphBlock: args.dump_block_graph,
            },
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
    dump: Optional[Dict[DumpType, Optional[TextIO]]] = None,
):
    if seed is not None:
        random.seed(seed)

    asset = Asset.load(stream, dump=dump)

    vis = GraphVisualizer(asset.blocks, asset.chunks, asset.extern)
    if dump and (dump_output := dump.get(DumpType.GraphBlock)):
        vis.generate_block_graph(dump_output)

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
