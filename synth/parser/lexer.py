from typing import Iterable, List, Optional

from .error import LexError
from .token import RESERVED_WORD_LOOKUP, Token, TokenType

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
    "&": TokenType.AddressOf,
    "+": TokenType.Plus,
    "-": TokenType.Minus,
    "*": TokenType.Times,
    # "/": TokenType.Divide,  # this one is more complex...
}


class Lexer:
    """
    Producer for tokens, given a valid and lexable program.
    """

    def __init__(self, stream: str):
        self.stream = stream

        self.n = -1
        self.ch = None
        self.ch_prev = None
        self._advance()

    def tokens(self) -> Iterable[Token]:
        """
        Utility method for extracting tokens performing a number of helpful
        transformations from the raw token() method.
        """

        last = None
        while True:
            token = self.token()
            if token is None:
                # skip missing tokens
                continue

            # de-duplicate newlines
            if token.ttype == TokenType.Newline:
                if last and last.ttype == TokenType.Newline:
                    continue

            yield token
            last = token

            # the last token of the stream should be an end-of-file
            if token.ttype == TokenType.EOF:
                break

    def tokens_list(self) -> List[Token]:
        """
        Utility method for extracting tokens to a list.
        """

        return list(self.tokens())

    def token(self) -> Optional[Token]:
        """
        Read a single token, consuming the input.

        If None is returned, this indicates a token was not created, however,
        some of the input stream should have been consumed. In this case, the
        consumer should simply skip to the next token. Generally, this is
        performed as an optimization to prevent extraneous loops or recursion
        within this function.
        """

        if self.ch is None:
            return Token(self.n, 1, TokenType.EOF)
        elif self.ch == "\n":
            n = self.n
            self._advance()
            while self._isspace() and self.ch != "\n":
                self._advance()
            return Token(n, 1, TokenType.Newline)
        elif self._isspace():
            while self._isspace() and self.ch != "\n":
                self._advance()
            return None
        elif ttype := SIMPLE_TOKENS.get(self.ch):
            self._advance()
            return Token(self.n, 1, ttype)
        elif self.ch == "/":
            self._advance()
            if self.ch == "/":
                # single line comment
                while self.ch is not None and self.ch != "\n":
                    self._advance()
                return self.token()
            elif self.ch == "*":
                # multi-line comment
                start = self.n
                while True:
                    self._advance()
                    if self.ch is None:
                        raise LexError(start, self.n, "unfinished comment")
                    elif self.ch == "*":
                        self._advance()
                        if self.ch == "/":
                            self._advance()
                            break

                return None
            else:
                # just a division operator
                return Token(self.n, 1, TokenType.Divide)
        elif self.ch == "'" or self.ch == '"':
            s = self._read_str()
            return Token(self.n, len(s) + 2, TokenType.String, s)
        elif self._isalpha() or self.ch == "$":
            n = self._read_name()
            if n in ("null", "NULL"):
                return Token(self.n, len(n), TokenType.Integer, 0)
            elif n in RESERVED_WORD_LOOKUP:
                return Token(
                    self.n, len(n), TokenType.Reserved, RESERVED_WORD_LOOKUP[n]
                )
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

        self._advance()
        while self._isalnum():
            self._advance()

        if self.ch is not None and not self._isspace() and self.ch not in SIMPLE_TOKENS:
            raise LexError(start, self.n, "invalid word")

        return self.stream[start : self.n]

    def _read_num(self) -> str:
        start = self.n

        self._advance()
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
