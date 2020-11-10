from enum import Enum, unique


@unique
class TokenType(Enum):
    Unknown = -1

    EOF = 0

    Newline = 1
    Dot = 2
    Comma = 3
    Colon = 4
    Semicolon = 5
    Equals = 6

    BracketOpen = 7
    BracketClose = 8
    ParenOpen = 9
    ParenClose = 10
    BraceOpen = 11
    BraceClose = 12

    Name = 15
    Reserved = 16
    String = 17
    Integer = 18

    AddressOf = 19

    Plus = 20
    Minus = 21
    Times = 22
    Divide = 23


class Token:
    def __init__(self, position: int, length: int, ttype: TokenType, lexeme: str = ""):
        self.position = position
        self.length = length
        self.ttype = ttype
        self.lexeme = lexeme

    def __str__(self):
        parts = []
        if self.ttype:
            parts.append(f"ttype={self.ttype}")
        if self.lexeme:
            parts.append(f"lexeme={self.lexeme}")
        return f"<Token {' '.join(parts)}>"
