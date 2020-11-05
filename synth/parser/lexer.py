from typing import Iterable, List, Optional

from .token import Token, TokenType
from .error import LexError

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


RESERVED_WORDS = {"chunk"}


class Lexer:
    def __init__(self, stream: str):
        self.stream = stream

        self.n = -1
        self.ch = None
        self.ch_prev = None
        self._advance()

    def tokens(self) -> Iterable[Token]:
        while token := self.token():
            yield token
            if token.ttype == TokenType.EOF:
                break

    def tokens_list(self) -> List[Token]:
        return list(self.tokens())

    def token(self) -> Optional[Token]:
        if self.ch is None:
            return Token(self.n, 1, TokenType.EOF)
        elif self.ch == "\n":
            while self._isspace():
                self._advance()
            return Token(self.n, 1, TokenType.Newline)
        elif self._isspace():
            while self._isspace() and self.ch != "\n":
                self._advance()
            return self.token()
        elif ttype := SIMPLE_TOKENS.get(self.ch):
            self._advance()
            if ttype in SIMPLE_ABSORBERS:
                while self._isspace():
                    self._advance()
            return Token(self.n, 1, ttype)
        elif self.ch == "'" or self.ch == '"':
            s = self._read_str()
            return Token(self.n, len(s) + 2, TokenType.String, s)
        elif self._isalpha():
            n = self._read_name()
            if n in RESERVED_WORDS:
                return Token(self.n, len(n), TokenType.Reserved, n)
            else:
                return Token(self.n, len(n), TokenType.Name, n)
        elif self._isnum():
            n = self._read_num()
            return Token(self.n, len(n), TokenType.Integer, n)
        else:
            self._advance()
            return Token(self.n, 1, TokenType.Unknown)

    def _read_name(self) -> str:
        start = self.n

        while self._isalnum():
            self._advance()

        if self.ch is not None and not self._isspace() and self.ch not in SIMPLE_TOKENS:
            raise LexError(start, self.n, "invalid word")

        return self.stream[start : self.n]

    def _read_num(self) -> str:
        start = self.n

        while self._isnum():
            self._advance()

        if self.ch is not None and not self._isspace() and self.ch not in SIMPLE_TOKENS:
            raise LexError(start, self.n, "invalid number")

        return self.stream[start : self.n]

    def _read_str(self) -> str:
        start = self.n
        quote = self.ch

        self._advance()
        while self.ch is not None and self.ch != "\n" and self.ch != quote:
            self._advance()

        if self.ch is None or self.ch == "\n":
            raise LexError(start, self.n - 1, "end of string not found")

        assert self.ch == quote
        self._advance()

        return self.stream[start + 1 : self.n - 1]

    def _advance(self):
        self.ch_prev = self.ch

        self.n += 1
        if self.n >= len(self.stream):
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
        return self.ch == "_" or "a" <= self.ch <= "z" or "A" <= self.ch <= "Z"

    def _isnum(self):
        if self.ch is None:
            return False
        return "0" <= self.ch <= "9"

    def _isalnum(self):
        if self.ch is None:
            return False
        return (
            self.ch == "_"
            or "a" <= self.ch <= "z"
            or "A" <= self.ch <= "Z"
            or "0" <= self.ch <= "9"
        )
