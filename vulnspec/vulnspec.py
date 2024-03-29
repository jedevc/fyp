import argparse
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path
from pprint import pformat
from typing import Any, Dict, Iterable, Optional, Tuple, Union

from .assets import Asset, AssetLoader
from .common.data import data_path
from .common.dump import DumpType
from .common.error import SynthError
from .common.names import rename_args, rename_blocks, rename_vars
from .config import Configuration
from .graph import CodeGen, Program
from .graph.visualizer import GraphVisualizer
from .interpret import Interpreter
from .markov import MarkovLoader
from .nops import NopTransformer
from .solve import SolveUtils


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_synth = subparsers.add_parser(
        "synth", help="synthesize a specification into C code"
    )
    parser_synth.set_defaults(action=action_synth)
    parser_synth.add_argument("inpath", type=Path)
    parser_synth.add_argument("outpath", type=Path)
    parser_synth.add_argument("--seed", help="random seed to use")
    parser_synth.add_argument(
        "--template", action="append", help="preset value of a template"
    )
    parser_synth.add_argument(
        "--no-file-comment",
        dest="file_comment",
        action="store_false",
        help="don't create a file header comment",
    )
    parser_synth.add_argument(
        "--format",
        choices=["none", "llvm", "google", "chromium", "mozilla", "webkit"],
        default="webkit",
        help="coding style to output",
    )

    SYNTH_DUMP_ARGS = [
        "--dump-tokens",
        "--dump-ast",
        "--dump-ast-diagram",
        "--dump-block-graph",
        "--dump-block-chunk-graph",
    ]
    for dump in SYNTH_DUMP_ARGS:
        parser_synth.add_argument(dump, type=Path)

    parser_build = subparsers.add_parser(
        "build", help="execute the build commands in a C file header"
    )
    parser_build.set_defaults(action=action_build)
    parser_build.add_argument("inpath", type=Path)

    parser_strip = subparsers.add_parser(
        "strip", help="strip out the build commands in a C file header"
    )
    parser_strip.set_defaults(action=action_strip_file_comment)
    parser_strip.add_argument("inpath", type=Path)
    parser_strip.add_argument("outpath", type=Path)

    parser_environ = subparsers.add_parser(
        "environ", help="synthesize a specification into an environment"
    )
    parser_environ.set_defaults(action=action_environment)
    parser_environ.add_argument("inpath", type=Path)
    parser_environ.add_argument("outpath", type=Path)
    parser_environ.add_argument("--seed", help="random seed to use")
    parser_environ.add_argument(
        "--template", action="append", help="preset value of a template"
    )
    parser_environ.add_argument(
        "--solution",
        action="store_true",
        help="generate a solution using a .solve.py file",
    )
    parser_environ.add_argument(
        "--extra", action="append", help="extra files to include in the environment"
    )
    parser_environ.add_argument(
        "--extra-src",
        action="store_true",
        help="include generated source code in the environment",
    )
    parser_environ.add_argument(
        "--format",
        choices=["none", "llvm", "google", "chromium", "mozilla", "webkit"],
        default="webkit",
        help="coding style to output",
    )

    args = parser.parse_args()

    if hasattr(args, "action"):
        sys.exit(args.action(args))
    else:
        parser.print_help()
        sys.exit(1)


def action_synth(args) -> int:
    stream = args.inpath.read_text()
    config = Configuration(args.outpath, stream)

    templates = {}
    if args.template:
        for templ in args.template:
            name, value = templ.split("=")
            templates[name] = value

    dump = {
        DumpType.Tokens: args.dump_tokens,
        DumpType.AST: args.dump_ast,
        DumpType.ASTDiagram: args.dump_ast_diagram,
        DumpType.GraphBlock: args.dump_block_graph,
        DumpType.GraphBlockChunk: args.dump_block_chunk_graph,
    }
    try:
        _, program = synthesize(stream, args.seed, templates, dump=dump)
    except SynthError as err:
        print(err, file=sys.stderr)
        return 1

    code = gen_code(program, config, file_comment=True, style=args.format)
    args.outpath.write_text(code)

    return 0


def action_build(args) -> int:
    stream = args.inpath.read_text()

    try:
        run_commands(stream, "build", args.inpath.parent)
    except KeyError as e:
        print(f"{e} commands not found in input file", file=sys.stderr)
        return 1

    return 0


def action_environment(args) -> int:
    stream = args.inpath.read_text()
    base = Path(args.inpath).parent

    args.outpath.mkdir(parents=True, exist_ok=True)
    target = args.outpath / "target.c"

    config = Configuration(target, stream)

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

    templates = {}
    if args.template:
        for templ in args.template:
            name, value = templ.split("=")
            templates[name] = value

    try:
        asset, program = synthesize(stream, args.seed, templates)
        code = gen_code(program, config, style=args.format)
        target.write_text(code)
    except SynthError as err:
        print(err, file=sys.stderr)
        return 1

    for command in config.build_commands(relative=True):
        subprocess.run(command, cwd=args.outpath, shell=True, check=True)

    if args.extra_src:
        copies[target.name] = target.name

    dockerfile = args.outpath / "Dockerfile"
    dockercode = config.environ.docker(
        config.dest_path.relative_to(args.outpath), copies
    )
    dockerfile.write_text(dockercode)

    if args.solution:
        script = args.inpath.with_suffix(".solve.py").read_text()
        result = gen_solve(script, asset.attachments, config)

        solvefile = args.outpath / "solve.py"
        solvefile.write_text(result)

    return 0


def action_strip_file_comment(args) -> int:
    lines = args.inpath.read_text().rstrip().split("\n")
    i = 0

    # ignore inputs that don't have a file header comment
    if not lines[i].startswith("/*"):
        return 0

    # skip past file header comment
    while True:
        try:
            i += 1
            line = lines[i]
        except IndexError:
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
            i += 1
            line = lines[i]
        except IndexError:
            break

        if line.strip():
            break

    # print all remaining lines
    args.outpath.write_text("\n".join(lines[i:]))

    return 0


def synthesize(
    spec: str,
    seed: Optional[str] = None,
    templates: Optional[Dict[str, Union[str, int, float, bool]]] = None,
    dump: Optional[Dict[DumpType, Optional[Path]]] = None,
) -> Tuple[Asset, Program]:
    if seed is not None:
        random.seed(seed)

    asset = Asset.load(spec, templates=templates, dump=dump)

    if dump and (dump_output := dump.get(DumpType.GraphBlock)):
        with dump_output.open("w") as f:
            vis = GraphVisualizer(f)
            vis.generate_block_graph(asset.blocks, asset.chunks, asset.extern)
    if dump and (dump_output := dump.get(DumpType.GraphBlockChunk)):
        with dump_output.open("w") as f:
            vis = GraphVisualizer(f)
            vis.generate_block_chunk_graph(asset.blocks, asset.chunks, asset.extern)

    nops = AssetLoader(data_path("nops")).list(external=True)
    noper = NopTransformer(nops)
    asset = noper.transform(asset)

    mapping = {}
    mloader = MarkovLoader(exclude=asset.extern.varnames)
    model_funcs = mloader.model("funcs", (3, 12))
    model_vars = mloader.model("vars", (1, 12))
    for block in asset.blocks:
        if block.name == "main":
            continue
        mapping[block.name] = model_funcs.generate()
    for chunk in asset.chunks:
        for var in chunk.variables:
            mapping[var.name] = model_vars.generate()

    rename_blocks(asset, mapping)
    rename_vars(asset, mapping)
    asset.attachments["names"] = mapping

    random.shuffle(asset.blocks)
    random.shuffle(asset.chunks)

    inter = Interpreter(asset)
    prog = inter.program()

    for func in prog.functions.values():
        fmapping = {}
        for var in func.args:
            fmapping[var.name] = model_vars.generate()
        rename_args(func, fmapping)

    return asset, prog


def gen_solve(source: str, annotations: Dict[str, Any], config: Configuration) -> str:
    binpath = config.debug_path if config.debug_path else config.dest_path
    with binpath.open("rb") as binary:
        su = SolveUtils(binary)

    items = {
        "filename": f"./{config.dest_path.name}",
        "var_locations": su.var_locations,
        **annotations,
    }

    pattern = re.compile(r"^gen_(\S+)\s*=.*$", flags=re.MULTILINE)

    def subf(match: re.Match) -> str:
        lhs = f"gen_{match.group(1)}"
        rhs = pformat(items[match.group(1)])
        return f"{lhs} = {rhs}"

    return pattern.sub(subf, source).rstrip()


def gen_code(
    program: Program,
    config: Configuration,
    file_comment: bool = False,
    style: str = "none",
) -> str:
    code = CodeGen(program).generate()
    if style != "none":
        proc = subprocess.run(
            ["clang-format", f"-style={style}"],
            input=code.encode(),
            stdout=subprocess.PIPE,
            check=True,
        )
        code = proc.stdout.decode()

    if file_comment:
        comment = "\n".join(
            [
                "/*",
                " * Generated by vulnspec.",
                " *",
                " * Build:",
                *[" > " + command for command in config.build_commands(absolute=True)],
                " */",
                "",
            ]
        )
        code = comment + code

    return code


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


def run_commands(stream: str, section: str, cwd: Optional[Path] = None):
    for command in extract_commands(stream, section):
        print(command, file=sys.stderr, flush=True)
        subprocess.run(command, cwd=cwd, shell=True, check=True)
