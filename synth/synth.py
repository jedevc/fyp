import argparse
import subprocess
import sys
from typing import Optional, TextIO

from .interpret import Interpreter
from .parser import Lexer, Parser, SynthError
from .passes import BlockifyVisitor, ChunkifyVisitor, PrinterVisitor, TypeCheckVisitor


def main() -> Optional[int]:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("infile", type=argparse.FileType("r"))
    arg_parser.add_argument("outfile", type=argparse.FileType("w"))
    arg_parser.add_argument(
        "--debug", choices=["print"], help="Perform debugging actions"
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
        synthesize(stream, args.outfile, debug=args.debug, style=args.format)
    except SynthError as err:
        print(err.format(stream), file=sys.stderr)
        return 1

    return 0


def synthesize(stream: str, output: TextIO, debug: str = "", style: str = "none"):
    lex = Lexer(stream)
    tokens = lex.tokens_list()

    parser = Parser(tokens)
    spec = parser.parse()

    if debug == "print":
        visitor = PrinterVisitor(sys.stderr)
        spec.accept(visitor)

    type_visitor = TypeCheckVisitor()
    spec.accept(type_visitor)

    chunk_visitor = ChunkifyVisitor()
    spec.accept(chunk_visitor)
    chunks = chunk_visitor.result()

    block_visitor = BlockifyVisitor(chunks)
    spec.accept(block_visitor)
    blocks = block_visitor.result()

    inter = Interpreter(blocks, chunks)
    prog = inter.program()
    code = prog.code

    if style == "none":
        print(code, file=output)
    else:
        subprocess.run(
            ["clang-format", f"-style={style}"],
            input=code.encode(),
            stdout=output,
            check=True,
        )
