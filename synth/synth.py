import argparse

from .parser import Lexer, LexError, ParseError, Parser
from .passes import PrinterVisitor


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
