from .parser import Lexer, LexError

data = """
chunk w : int
chunk x : int
chunk y : int,
      z : int
""".strip()


def main():
    lex = Lexer(data)

    try:
        for token in lex.tokens():
            print(str(token))
    except LexError as e:
        print(e.format())
