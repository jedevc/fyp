from typing import Iterable
from .token import Token, TokenType

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
    def __init__(self, stream: Iterable[str]):
        self.stream = stream

        self.done = False

        self.ch = None
        self.ch_prev = None
        self._advance()

    def next(self) -> Token:
        if self.done:
            return

        if self.ch is None:
            self.done = True
            return Token(TokenType.EOF)

        if self.ch == '\n':
            while self._isspace():
                self._advance()
            return Token(TokenType.Newline)
        elif self._isspace():
            while self._isspace():
                self._advance()
            return self.next()
        elif (ttype := SIMPLE_TOKENS.get(self.ch)):
            self._advance()
            if ttype in SIMPLE_ABSORBERS:
                while self._isspace():
                    self._advance()
            return Token(ttype)
        elif self.ch == '\'' or self.ch == '"':
            return Token(TokenType.String, self._read_str())
        elif self._isalpha():
            return Token(TokenType.Name, self._read_name())

        self._advance()
        return Token(TokenType.Unknown)

    def _read_name(self) -> str:
        s = []

        while self._isalnum():
            s.append(self.ch)
            self._advance()

        if self.ch is not None and not self._isspace() and self.ch not in SIMPLE_TOKENS:
            raise LexError("invalid word")

        return ''.join(s)

    def _read_str(self) -> str:
        quote = self.ch
        s = []

        self._advance()
        while self.ch is not None and self.ch != '\n' and self.ch != quote:
            s.append(self.ch)
            self._advance()

        if self.ch is None or self.ch == '\n':
            raise LexError("end of string not found")

        assert self.ch == quote
        self._advance()

        return ''.join(s)

    def _advance(self):
        try:
            self.ch_prev = self.ch
            self.ch = next(self.stream)
        except StopIteration:
            self.ch = None

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
        return 'a' <= self.ch <= 'z' or 'A' <= self.ch <= 'Z' or '0' <= self.ch <= 'Z'

class LexError(RuntimeError):
    pass
