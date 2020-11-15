import argparse

from .parser import Lexer, LexError, ParseError, ProcessingError, Parser
from .passes import PrinterVisitor, ChunkifyVisitor


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

    for token in tokens:
        print(str(token))

    parser = Parser(tokens)
    try:
        spec = parser.parse()
    except ParseError as err:
        print(err.format(stream))
        return
    print(spec)

    visitor = PrinterVisitor()
    spec.accept(visitor)
    print(spec.blocks[0].token_start)

    try:
        visitor = ChunkifyVisitor()
        chunk = spec.accept(visitor)
        print(chunk)
    except ProcessingError as err:
        print(err.format(stream))
        return

    # print(chunk)
    # chunk[-1].add(Variable("test", "int", 1))
    # print(str(chunk[-1].constraint))

    # for var in chunk[-1].variables:
    #     print(var.name)
