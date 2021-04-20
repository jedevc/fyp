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
    Template = 15
    String = 16
    Integer = 17
    Float = 18

    Plus = 19
    Minus = 20
    Times = 21
    Divide = 22

    CompareEQ = 23
    CompareNE = 24
    CompareLT = 25
    CompareGT = 26
    CompareLE = 27
    CompareGE = 28

    Ellipsis = 29
    Literal = 30

    BitwiseAnd = 31
    BitwiseOr = 32
    BitwiseNot = 33
    BooleanAnd = 34
    BooleanOr = 35
    BooleanNot = 36


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
    TokenType.Template: "template",
    TokenType.String: "string",
    TokenType.Integer: "integer",
    TokenType.Float: "float",
    TokenType.Plus: "plus",
    TokenType.Minus: "minus",
    TokenType.Times: "times",
    TokenType.Divide: "divide",
    TokenType.CompareEQ: "equals",
    TokenType.CompareNE: "not equals",
    TokenType.CompareLT: "less than",
    TokenType.CompareGT: "greater than",
    TokenType.CompareLE: "less than or equal to",
    TokenType.CompareGE: "greater than or equal to",
    TokenType.Ellipsis: "ellipsis",
    TokenType.Literal: "literal",
    TokenType.BitwiseAnd: "bitwise and",
    TokenType.BitwiseOr: "bitwise or",
    TokenType.BitwiseNot: "bitwise not",
    TokenType.BooleanNot: "boolean not",
    TokenType.BooleanOr: "boolean or",
    TokenType.BooleanNot: "boolean not",
}


class ReservedWord:
    Block = "block"
    Chunk = "chunk"
    Extern = "extern"
    Template = "template"

    Function = "fn"

    Call = "call"

    If = "if"
    Else = "else"
    While = "while"

    As = "as"

    SizeOf = "sizeof"
    SizeOfExpr = "sizeofexpr"


RESERVED_WORDS = {
    ReservedWord.Block,
    ReservedWord.Chunk,
    ReservedWord.Extern,
    ReservedWord.Template,
    ReservedWord.Function,
    ReservedWord.Call,
    ReservedWord.If,
    ReservedWord.Else,
    ReservedWord.While,
    ReservedWord.As,
    ReservedWord.SizeOf,
    ReservedWord.SizeOfExpr,
}


class Token:
    """
    The atomic building-block of the underlying code.
    """

    def __init__(
        self,
        stream: str,
        position: int,
        length: int,
        ttype: TokenType,
        lexeme: Any = "",
    ):
        self.stream = stream
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
