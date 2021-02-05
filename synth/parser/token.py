from enum import Enum, unique
from typing import Any


@unique
class TokenType(Enum):
    Unknown = -1

    EOF = 0

    Newline = 1
    Dot = 2
    Comma = 3
    Colon = 4
    Semicolon = 5
    Assign = 6

    BracketOpen = 7
    BracketClose = 8
    ParenOpen = 9
    ParenClose = 10
    BraceOpen = 11
    BraceClose = 12

    Name = 13
    Reserved = 14
    String = 15
    Integer = 16
    Float = 17

    Plus = 18
    Minus = 19
    Times = 20
    Divide = 21

    CompareEQ = 22
    CompareNE = 23
    CompareLT = 24
    CompareGT = 25
    CompareLE = 26
    CompareGE = 27

    Negate = 28

    Ellipsis = 29
    Literal = 30

    And = 31
    BooleanAnd = 32
    Or = 33
    BooleanOr = 34


PRINTABLE_NAMES = {
    TokenType.Unknown: "unknown",
    TokenType.EOF: "EOF",
    TokenType.Newline: "newline",
    TokenType.Dot: "dot",
    TokenType.Comma: "comma",
    TokenType.Colon: "colon",
    TokenType.Semicolon: "semicolon",
    TokenType.Assign: "assign",
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
    TokenType.Float: "float",
    TokenType.Plus: "plus",
    TokenType.Minus: "minus",
    TokenType.Times: "times",
    TokenType.Divide: "divide",
    TokenType.Negate: "negate",
    TokenType.CompareEQ: "equals",
    TokenType.CompareNE: "not equals",
    TokenType.CompareLT: "less than",
    TokenType.CompareGT: "greater than",
    TokenType.CompareLE: "less than or equal to",
    TokenType.CompareGE: "greater than or equal to",
    TokenType.Ellipsis: "ellipsis",
    TokenType.Literal: "literal",
    TokenType.And: "and",
    TokenType.BooleanAnd: "boolean and",
    TokenType.Or: "or",
    TokenType.BooleanOr: "boolean or",
}


class ReservedWord:
    Block = "block"
    Chunk = "chunk"
    Extern = "extern"

    Function = "fn"

    Call = "call"

    If = "if"
    Else = "else"
    While = "while"

    As = "as"


RESERVED_WORDS = {
    ReservedWord.Block,
    ReservedWord.Chunk,
    ReservedWord.Extern,
    ReservedWord.Function,
    ReservedWord.Call,
    ReservedWord.If,
    ReservedWord.Else,
    ReservedWord.While,
    ReservedWord.As,
}


class Token:
    """
    The atomic building-block of the underlying code.
    """

    def __init__(self, position: int, length: int, ttype: TokenType, lexeme: Any = ""):
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
