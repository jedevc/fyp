import itertools
from typing import Iterable, List, Optional

from .token import Token, TokenType

SIMPLE_TOKENS = {
    ".": TokenType.Dot,
    ",": TokenType.Comma,
    ":": TokenType.Colon,
    ";": TokenType.Semicolon,
    "=": TokenType.Equals,
    "[": TokenType.BracketOpen,
    "]": TokenType.BracketClose,
    "(": TokenType.ParenOpen,
    ")": TokenType.ParenClose,
    "{": TokenType.BraceOpen,
    "}": TokenType.BraceClose,
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

    def tokens(self) -> Iterable[Token]:
        while token := self.token():
            yield token

    def tokens_list(self) -> List[Token]:
        return list(self.tokens())

    def token(self) -> Optional[Token]:
        if self.done:
            return None

        if self.ch is None:
            self.done = True
            return Token(self.n, TokenType.EOF)

        if self.ch == "\n":
            while self._isspace():
                self._advance()
            return Token(self.n, TokenType.Newline)
        elif self._isspace():
            while self._isspace():
                self._advance()
            return self.token()
        elif ttype := SIMPLE_TOKENS.get(self.ch):
            self._advance()
            if ttype in SIMPLE_ABSORBERS:
                while self._isspace():
                    self._advance()
            return Token(self.n, ttype)
        elif self.ch == "'" or self.ch == '"':
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
            raise LexError(self.stream, "invalid word", start=start, end=self.n)

        return self.stream[start : self.n]

    def _read_str(self) -> str:
        start = self.n
        quote = self.ch

        self._advance()
        while self.ch is not None and self.ch != "\n" and self.ch != quote:
            self._advance()

        if self.ch is None or self.ch == "\n":
            raise LexError(
                self.stream, "end of string not found", start=start, end=self.n - 1
            )

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
        return self.ch in (" ", "\t", "\n")

    def _isalpha(self):
        if self.ch is None:
            return False
        return "a" <= self.ch <= "z" or "A" <= self.ch <= "Z"

    def _isalnum(self):
        if self.ch is None:
            return False
        return "a" <= self.ch <= "z" or "A" <= self.ch <= "Z" or "0" <= self.ch <= "9"


class LexError(BaseException):
    def __init__(self, stream: str, msg: str, start: int, end: int):
        super().__init__()
        self.location = LexErrorLocation(stream, start, end)
        self.msg = msg

    def format(self):
        return "\n".join(
            [
                f"Error: {self.msg}",
                "",
                self.location.format(),
            ]
        )


class LexErrorLocation:
    def __init__(self, stream: str, start: int, end: int):
        assert start <= end

        self.start_line = 1
        self.start_column = 1
        for i in range(start):
            if stream[i] == "\n":
                self.start_column = 1
                self.start_line += 1
            else:
                self.start_column += 1
        self.end_line = 1
        self.end_column = 1
        for i in range(end):
            if stream[i] == "\n":
                self.end_column = 1
                self.end_line += 1
            else:
                self.end_column += 1

        self.lines = list(zip(itertools.count(), stream.split("\n")))

    def format(self):
        CONTEXT = 3

        parts = []
        for i, line in self.lines[max(0, self.end_line - CONTEXT) : self.end_line]:
            prefix = f"  {str(i).rjust(6)}  |  "
            parts.append(f"{prefix}{line}")

        if self.start_line == self.end_line:
            parts.append(
                f"{len(prefix) * ' '}{(self.start_column - 1) * ' '}{(self.end_column - self.start_column) * '-'}^"
            )
        else:
            parts.append(f"{len(prefix) * ' '}{(self.end_column - 1) * '-'}^")
        return "\n".join(parts)
