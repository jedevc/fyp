import argparse

from .interpret import Interpreter
from .parser import Lexer, LexError, ParseError, Parser, ProcessingError
from .passes import BlockifyVisitor, ChunkifyVisitor, PrinterVisitor, TypeCheckVisitor


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", type=argparse.FileType("r"))
    args = parser.parse_args()

    stream = args.infile.read()

    lex = Lexer(stream)
    try:
        tokens = lex.tokens_list()
    except LexError as err:
        print(err.format(stream))
        return

    parser = Parser(tokens)
    try:
        spec = parser.parse()
    except ParseError as err:
        print(err.format(stream))
        return

    visitor = PrinterVisitor()
    spec.accept(visitor)
    print("-" * 50)

    try:
        visitor = TypeCheckVisitor()
        spec.accept(visitor)
    except ProcessingError as err:
        print(err.format(stream))
        return

    try:
        visitor = ChunkifyVisitor()
        spec.accept(visitor)
        chunks = visitor.result()
    except ProcessingError as err:
        print(err.format(stream))
        return

    try:
        visitor = BlockifyVisitor(chunks)
        blocks = spec.accept(visitor)
    except ProcessingError as err:
        print(err.format(stream))
        return

    inter = Interpreter(blocks, chunks)
    prog = inter.program()
    print(prog.code)

    # print(chunk)
    # chunk[-1].add(Variable("test", "int", 1))
    # print(str(chunk[-1].constraint))

    # for var in chunk[-1].variables:
    #     print(var.name)
