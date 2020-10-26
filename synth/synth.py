from .parser import Lexer, LexError, Parser

data = """
chunk w : int
chunk x : int
chunk y : int,
      z : int
""".strip()


def main():
    lex = Lexer(data)
    tokens = lex.tokens_list()
    for token in tokens:
        print(str(token))

    parser = Parser(tokens)
    spec = parser.spec()
    print(spec)
