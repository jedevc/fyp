from typing import Any
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
    String = 16

class Token:
    def __init__(self, position: int, ttype: TokenType, lexeme: str = "", obj: Any = None):
        self.position = position
        self.ttype = ttype
        self.lexeme = lexeme
        self.obj = obj

    def __str__(self):
        parts = []
        if self.ttype:
            parts.append(f"ttype={self.ttype}")
        if self.lexeme:
            parts.append(f"lexeme={self.lexeme}")
        if self.obj:
            parts.append(f"lexeme={str(self.obj)}")
        return f"<Token {' '.join(parts)}>"
