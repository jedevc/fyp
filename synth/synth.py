from .parser import Lexer, LexError, ParseError, Parser

data = """
chunk w : int
chunk x : int
chunk y : int,
      z : int
""".strip()


def main():
    lex = Lexer(data)
    try:
        tokens = lex.tokens_list()
    except LexError as err:
        print(err.format(data))
        return

    for token in tokens:
        print(str(token))

    parser = Parser(tokens)
    try:
        spec = parser.parse()
    except ParseError as err:
        print(err.format(data))
        return
    print(spec)
