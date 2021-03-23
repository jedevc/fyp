import argparse
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, Optional, TextIO

from .assets import Asset, AssetLoader
from .common.dump import DumpType
from .common.error import SynthError
from .common.names import rename_blocks, rename_vars
from .config import Configuration
from .graph import CodeGen
from .graph.visualizer import GraphVisualizer
from .interpret import Interpreter
from .markov import Markov, ModelFuncs, ModelVars
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

    SYNTH_DUMP_ARGS = [
        "--dump-ast",
        "--dump-ast-diagram",
        "--dump-block-graph",
        "--dump-block-chunk-graph",
    ]
    for dump in SYNTH_DUMP_ARGS:
        parser_synth.add_argument(dump, type=argparse.FileType("w"))

    parser_build = subparsers.add_parser("build")
    parser_build.set_defaults(action=action_build)
    parser_build.add_argument("infile", type=argparse.FileType("r"))

    parser_strip = subparsers.add_parser("strip")
    parser_strip.set_defaults(action=action_strip_file_comment)
    parser_strip.add_argument("infile", type=argparse.FileType("r"))
    parser_strip.add_argument("outfile", type=argparse.FileType("w"))

    parser_environ = subparsers.add_parser("environ")
    parser_environ.set_defaults(action=action_environment)
    parser_environ.add_argument("infile", type=argparse.FileType("r"))
    parser_environ.add_argument("outpath", type=Path)
    parser_environ.add_argument("--seed", help="Random seed to use")
    parser_environ.add_argument(
        "--extra", action="append", help="Extra files to include"
    )
    parser_environ.add_argument(
        "--extra-src", action="store_true", help="Include generated source code"
    )
    parser_environ.add_argument(
        "--format",
        choices=["none", "llvm", "google", "chromium", "mozilla", "webkit"],
        default="webkit",
        help="Coding style to output",
    )

    args = parser.parse_args()

    if hasattr(args, "action"):
        return args.action(args)
    else:
        parser.print_help()
        return 1


def action_synth(args) -> int:
    stream = args.infile.read()

    try:
        synthesize(
            stream,
            args.outfile,
            Configuration(stream),
            args.seed,
            style=args.format,
            dump={
                DumpType.AST: args.dump_ast,
                DumpType.ASTDiagram: args.dump_ast_diagram,
                DumpType.GraphBlock: args.dump_block_graph,
                DumpType.GraphBlockChunk: args.dump_block_chunk_graph,
            },
            file_comment=args.file_comment,
        )
    except SynthError as err:
        print(err, file=sys.stderr)
        return 1

    return 0


def action_build(args) -> int:
    stream = args.infile.read()

    try:
        run_commands(stream, "build")
    except KeyError as e:
        print(f"{e} commands not found in input file", file=sys.stderr)
        return 1

    return 0


def action_environment(args) -> int:
    stream = args.infile.read()
    base = Path(args.infile.name).parent

    args.outpath.mkdir(parents=True, exist_ok=True)

    config = Configuration(stream)

    for fname in config.config["files"]:
        dstp = args.outpath / fname
        srcp = base / fname
        shutil.copy(srcp, dstp)

    copies = {}
    if args.extra:
        for fname in args.extra:
            if ":" in fname:
                src, dst = fname.split(":", maxsplit=1)
                docker_src = Path(src.lstrip("/"))
                docker_dst = Path(dst)

                actual_src = Path(src)
                actual_dst = args.outpath / Path(dst.lstrip("/"))
            else:
                actual_src = Path(fname)
                actual_dst = args.outpath / actual_src.name

                docker_src = Path(actual_src.name)
                docker_dst = Path(actual_src.name)

            actual_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(actual_src, actual_dst)

            copies[docker_src] = docker_dst

    target = args.outpath / "target.c"
    try:
        with target.open("w") as f:
            synthesize(
                stream,
                f,
                config,
                args.seed,
                style=args.format,
            )
    except SynthError as err:
        print(err, file=sys.stderr)
        return 1

    for command in config.build_commands(target):
        subprocess.run(command, shell=True, check=True)

    if args.extra_src:
        copies[target.name] = target.name

    dockerfile = args.outpath / "Dockerfile"
    with dockerfile.open("w") as f:
        config.environ.docker(
            config.build_output(target).relative_to(args.outpath), copies, f
        )

    return 0


def action_strip_file_comment(args) -> int:
    lines = args.infile

    # ignore inputs that don't have a file header comment
    if not next(lines).startswith("/*"):
        return 0

    # skip past file header comment
    while True:
        try:
            line = next(lines)
        except StopIteration:
            print(
                "unexpected end of file while parsing header comment", file=sys.stderr
            )
            return 1

        if line.startswith(" */"):
            break

        if line.startswith(" *") or line.startswith(" >"):
            continue

        print("unexpected line prefix while parsing header comment", file=sys.stderr)
        return 1

    # strip whitespace
    while True:
        try:
            line = next(lines)
        except StopIteration:
            break

        if line.strip():
            args.outfile.write(line)
            break

    # print all remaining lines
    for line in lines:
        args.outfile.write(line)

    return 0


def synthesize(
    stream: str,
    output: TextIO,
    config: Configuration,
    seed: Optional[str] = None,
    style: str = "none",
    dump: Optional[Dict[DumpType, Optional[TextIO]]] = None,
    file_comment: bool = False,
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

    mapping = {}
    model_vars = Markov(ModelVars.TABLE, ModelVars.SIZE, ModelVars.TERMINAL)
    model_funcs = Markov(ModelFuncs.TABLE, ModelFuncs.SIZE, ModelFuncs.TERMINAL)
    for block in asset.blocks:
        if block.name == "main":
            continue
        mapping[block.name] = model_funcs.generate()
    for chunk in asset.chunks:
        for var in chunk.variables:
            mapping[var.name] = model_vars.generate()

    rename_blocks(asset, mapping)
    rename_vars(asset, mapping)

    inter = Interpreter(asset)
    prog = inter.program()
    gen = CodeGen(prog)
    code = gen.generate()

    if file_comment:
        comment = "\n".join(
            [
                "/*",
                " * Generated by vulnspec.",
                " *",
                " * Build:",
                *[
                    " > " + command
                    for command in config.build_commands(Path(output.name))
                ],
                " */",
                "",
            ]
        )
        print(comment, file=output, flush=True)

    if style == "none":
        print(code, file=output, flush=True)
    else:
        subprocess.run(
            ["clang-format", f"-style={style}"],
            input=code.encode(),
            stdout=output,
            check=True,
        )


def extract_commands(stream: str, section: str) -> Iterable[str]:
    match = re.search(
        r"/\*.*" + section + r":((?:\s*>\s*[^\n]*\n)+)",
        stream,
        re.MULTILINE | re.IGNORECASE | re.DOTALL,
    )
    if not match:
        raise KeyError(section)
    if "*/" in match.group(0):
        raise KeyError(section)

    for command in match.group(1).split("\n"):
        command = command.split(">")[-1].strip()
        if not command:
            continue

        yield command


def run_commands(stream: str, section: str):
    for command in extract_commands(stream, section):
        print(command, file=sys.stderr, flush=True)
        subprocess.run(command, shell=True, check=True)
