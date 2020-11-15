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


PRINTABLE_NAMES = {
    TokenType.Newline: "newline",
    TokenType.Dot: "dot",
    TokenType.Comma: "comma",
    TokenType.Colon: "colon",
    TokenType.Semicolon: "semicolon",
    TokenType.Equals: "equals",
    TokenType.BracketOpen: "opening square bracket",
    TokenType.BracketClose: "closing square bracket",
    TokenType.ParenOpen: "opening paranthesis",
    TokenType.ParenClose: "closing paranethesis",
    TokenType.BraceOpen: "opening curly brace",
    TokenType.BraceClose: "closing curly brace",
    TokenType.Name: "name",
    TokenType.Reserved: "reserved name",
    TokenType.String: "string",
    TokenType.Integer: "integer",
    TokenType.AddressOf: "address",
    TokenType.Plus: "plus",
    TokenType.Minus: "minus",
    TokenType.Times: "times",
    TokenType.Divide: "divide1",
}


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
