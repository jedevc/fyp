from .parser import Lexer, LexError

data = """
chunk w : int
chunk x : int
chunk y : int,
      z : int
""".strip()

from .parser.lexer import LexErrorLocation

def main():
    lex = Lexer(data)

    try:
        while (token := lex.next()):
            print(str(token))
    except LexError as e:
        print(e.format())
