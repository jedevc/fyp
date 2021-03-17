import argparse
import random
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, TextIO

from .assets import Asset, AssetLoader
from .compile import CompilerConfig
from .dump import DumpType
from .error import SynthError
from .graph import CodeGen
from .graph.visualizer import GraphVisualizer
from .interpret import Interpreter
from .nops import NopTransformer


def main() -> Optional[int]:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_synth = subparsers.add_parser("synth")
    parser_synth.set_defaults(action=action_synth)
    parser_synth.add_argument("infile", type=argparse.FileType("r"))
    parser_synth.add_argument("outfile", type=argparse.FileType("w"))
    parser_synth.add_argument("--seed", help="Random seed to use")
    parser_synth.add_argument(
        "--no-file-comment",
        dest="file_comment",
        action="store_false",
        help="Don't create a file header comment",
    )
    parser_synth.add_argument(
        "--format",
        choices=["none", "llvm", "google", "chromium", "mozilla", "webkit"],
        default="webkit",
        help="Coding style to output",
    )
    for dump in SYNTH_DUMP_ARGS:
        parser_synth.add_argument(dump, type=argparse.FileType("w"))

    build_synth = subparsers.add_parser("build")
    build_synth.set_defaults(action=action_build)
    build_synth.add_argument("infile", type=argparse.FileType("r"))

    args = parser.parse_args()

    if hasattr(args, "action"):
        return args.action(args)
    else:
        parser.print_help()
        return 1


SYNTH_DUMP_ARGS = [
    "--dump-ast",
    "--dump-ast-diagram",
    "--dump-block-graph",
    "--dump-block-chunk-graph",
]


def action_synth(args) -> int:
    stream = args.infile.read()

    conf = CompilerConfig(stream)
    if args.file_comment:
        prefix = "\n".join(
            [
                "/*",
                " * Generated by vulnspec.",
                " *",
                " * Build:",
                *[
                    " > " + command
                    for command in conf.commands(Path(args.outfile.name))
                ],
                " */",
                "",
            ]
        )
    else:
        prefix = ""

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
                DumpType.GraphBlockChunk: args.dump_block_chunk_graph,
            },
            prefix=prefix,
        )
    except SynthError as err:
        print(err, file=sys.stderr)
        return 1

    return 0


def action_build(args) -> int:
    stream = args.infile.read()

    match = re.search(r"Build:((?:\s*>\s*.*\n)+)", stream, re.MULTILINE)
    if not match:
        print("Cannot file build command in target file", file=sys.stderr)
        return 1

    for command in match.group(1).split("\n"):
        command = command.split(">")[-1].strip()
        if not command:
            continue

        print(command)
        subprocess.run(command, shell=True, check=True)

    return 0


def synthesize(
    stream: str,
    output: TextIO,
    seed: Optional[str] = None,
    style: str = "none",
    dump: Optional[Dict[DumpType, Optional[TextIO]]] = None,
    prefix: str = "",
):
    if seed is not None:
        random.seed(seed)

    asset = Asset.load(stream, dump=dump)

    if dump and (dump_output := dump.get(DumpType.GraphBlock)):
        vis = GraphVisualizer(dump_output)
        vis.generate_block_graph(asset.blocks, asset.chunks, asset.extern)
    if dump and (dump_output := dump.get(DumpType.GraphBlockChunk)):
        vis = GraphVisualizer(dump_output)
        vis.generate_block_chunk_graph(asset.blocks, asset.chunks, asset.extern)

    nops = AssetLoader.list("nops", external=True)
    noper = NopTransformer(nops)
    asset = noper.transform(asset)

    inter = Interpreter(asset)
    prog = inter.program()
    gen = CodeGen(prog)
    code = gen.generate()

    if prefix:
        print(prefix, file=output, flush=True)

    if style == "none":
        print(code, file=output, flush=True)
    else:
        subprocess.run(
            ["clang-format", f"-style={style}"],
            input=code.encode(),
            stdout=output,
            check=True,
        )
