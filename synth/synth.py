import argparse
import sys
from typing import Optional

from .interpret import Interpreter
from .parser import Lexer, LexError, ParseError, Parser, ProcessingError
from .passes import BlockifyVisitor, ChunkifyVisitor, PrinterVisitor, TypeCheckVisitor


def main() -> Optional[int]:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("infile", type=argparse.FileType("r"))
    arg_parser.add_argument("outfile", type=argparse.FileType("w"))
    arg_parser.add_argument(
        "--debug", choices=["print"], help="Perform debugging actions"
    )
    args = arg_parser.parse_args()

    stream = args.infile.read()

    try:
        lex = Lexer(stream)
        tokens = lex.tokens_list()

        parser = Parser(tokens)
        spec = parser.parse()
    except (LexError, ParseError) as err:
        print(err.format(stream), file=sys.stderr)
        return 1

    if args.debug == "print":
        visitor = PrinterVisitor(sys.stderr)
        spec.accept(visitor)

    try:
        type_visitor = TypeCheckVisitor()
        spec.accept(type_visitor)
    except ProcessingError as err:
        print(err.format(stream), file=sys.stderr)
        return 1

    try:
        chunk_visitor = ChunkifyVisitor()
        spec.accept(chunk_visitor)
        chunks = chunk_visitor.result()

        block_visitor = BlockifyVisitor(chunks)
        blocks = spec.accept(block_visitor)
    except ProcessingError as err:
        print(err.format(stream), file=sys.stderr)
        return 1

    inter = Interpreter(blocks, chunks)
    prog = inter.program()
    print(prog.code, file=args.outfile)

    return 0
