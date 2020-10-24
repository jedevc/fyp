from .parser import Lexer

data = """
chunk w : int
chunk x : int
chunk y : int,
      z : int
""".strip()

def main():
    lex = Lexer(iter(data))

    while (token := lex.next()):
        print(str(token))
