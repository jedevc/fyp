from typing import Iterable
from .token import Token, TokenType
import itertools

SIMPLE_TOKENS = {
    '.': TokenType.Dot,
    ',': TokenType.Comma,
    ':': TokenType.Colon,
    ';': TokenType.Semicolon,
    '=': TokenType.Equals,
    '[': TokenType.BracketOpen,
    ']': TokenType.BracketClose,
    '(': TokenType.ParenOpen,
    ')': TokenType.ParenClose,
    '{': TokenType.BraceOpen,
    '}': TokenType.BraceClose,
}
SIMPLE_ABSORBERS = [
    TokenType.Comma,
    TokenType.ParenOpen,
    TokenType.BracketOpen,
    TokenType.BraceOpen,
]

class Lexer:
    def __init__(self, stream: str):
        self.stream = stream

        self.n = -1
        self.done = False
        self.ch = None
        self.ch_prev = None
        self._advance()
    
    def next(self) -> Token:
        if self.done:
            return

        if self.ch is None:
            self.done = True
            return Token(self.n, TokenType.EOF)

        if self.ch == '\n':
            while self._isspace():
                self._advance()
            return Token(self.n, TokenType.Newline)
        elif self._isspace():
            while self._isspace():
                self._advance()
            return self.next()
        elif (ttype := SIMPLE_TOKENS.get(self.ch)):
            self._advance()
            if ttype in SIMPLE_ABSORBERS:
                while self._isspace():
                    self._advance()
            return Token(self.n, ttype)
        elif self.ch == '\'' or self.ch == '"':
            return Token(self.n, TokenType.String, self._read_str())
        elif self._isalpha():
            return Token(self.n, TokenType.Name, self._read_name())

        self._advance()
        return Token(self.n, TokenType.Unknown)

    def _read_name(self) -> str:
        start = self.n

        while self._isalnum():
            self._advance()

        if self.ch is not None and not self._isspace() and self.ch not in SIMPLE_TOKENS:
            raise LexError(self.stream, self.n, "invalid word")

        return self.stream[start : self.n]

    def _read_str(self) -> str:
        start = self.n
        quote = self.ch

        self._advance()
        while self.ch is not None and self.ch != '\n' and self.ch != quote:
            self._advance()

        if self.ch is None or self.ch == '\n':
            raise LexError(self.stream, start, "end of string not found")

        assert self.ch == quote
        self._advance()

        return self.stream[start + 1 : self.n - 1]

    def _advance(self):
        self.ch_prev = self.ch

        self.n += 1
        if self.n >= len(self.stream):
            self.done = True
            self.ch = None
        else:
            self.ch = self.stream[self.n]

    def _isspace(self):
        if self.ch is None:
            return False
        return self.ch in (' ', '\t', '\n')

    def _isalpha(self):
        if self.ch is None:
            return False
        return 'a' <= self.ch <= 'z' or 'A' <= self.ch <= 'Z'

    def _isalnum(self):
        if self.ch is None:
            return False
        return 'a' <= self.ch <= 'z' or 'A' <= self.ch <= 'Z' or '0' <= self.ch <= '9'

class LexError(BaseException):
    def __init__(self, stream: str, position: int, msg: str):
        self.location = LexErrorLocation(stream, position)
        self.msg = msg

    def format(self):
        return "\n".join([
            f"Error: {self.msg}",
            "",
            self.location.format(),
        ])

class LexErrorLocation:
    def __init__(self, stream: str, position: int):
        self.lines = list(zip(itertools.count(), stream.split('\n')))

        self.line_number = 1
        self.column_number = 1

        for i in range(position):
            if stream[i] == '\n':
                self.column_number = 1
                self.line_number += 1
            else:
                self.column_number += 1

    def format(self):
        CONTEXT = 3

        parts = []
        for i, line in self.lines[self.line_number - CONTEXT:self.line_number]:
            prefix = f"  {str(i).rjust(6)}  |  "
            parts.append(f"{prefix}{line}")

        parts.append(f"{len(prefix) * ' '}{(self.column_number - 1) * '-'}^")
        return '\n'.join(parts)
