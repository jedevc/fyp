import string
from typing import Dict, Iterable, List, Optional, Tuple, Union

from .error import LexError
from .token import RESERVED_WORDS, Token, TokenType

SIMPLE_TOKENS: Dict[str, Union[TokenType, Dict[str, TokenType]]] = {
    ".": {
        "...": TokenType.Ellipsis,
        ".": TokenType.Dot,
    },
    ",": TokenType.Comma,
    ":": TokenType.Colon,
    ";": TokenType.Semicolon,
    "=": {
        "==": TokenType.CompareEQ,
        "=": TokenType.Assign,
    },
    ">": {
        ">=": TokenType.CompareGE,
        ">": TokenType.CompareGT,
    },
    "<": {
        "<=": TokenType.CompareLE,
        "<": TokenType.CompareLT,
    },
    "!": {
        "!=": TokenType.CompareNE,
        "!": TokenType.BooleanNot,
    },
    "&": {
        "&&": TokenType.BooleanAnd,
        "&": TokenType.BitwiseAnd,
    },
    "|": {
        "||": TokenType.BooleanOr,
        "|": TokenType.BitwiseOr,
    },
    "~": TokenType.BitwiseNot,
    "[": TokenType.BracketOpen,
    "]": TokenType.BracketClose,
    "(": TokenType.ParenOpen,
    ")": TokenType.ParenClose,
    "{": TokenType.BraceOpen,
    "}": TokenType.BraceClose,
    "+": TokenType.Plus,
    "-": TokenType.Minus,
    "*": TokenType.Times,
    "/": TokenType.Divide,  # this one is more complex...
}


class Lexer:
    """
    Producer for tokens, given a valid and lexable program.
    """

    def __init__(self, stream: str):
        self.stream = stream

        self.n = -1
        self.ch: Optional[str] = None
        self.ch_prev: Optional[str] = None
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

        prevn = self.n

        if self.ch is None:
            return Token(self.stream, self.n, 1, TokenType.EOF)
        elif self.ch == "\n":
            n = self.n
            self._advance()
            while self._isspace() and self.ch != "\n":
                self._advance()
            return Token(self.stream, n, 1, TokenType.Newline)
        elif self._isspace():
            while self._isspace() and self.ch != "\n":
                self._advance()
            return None
        elif self.ch == "$":
            self._advance()
            if self.ch == "(":
                self._advance()

                start = self.n
                opened = 1
                while opened != 0:
                    if self.ch is None:
                        raise LexError(self.stream, start, self.n, "unfinished literal")
                    elif self.ch == "(":
                        opened += 1
                    elif self.ch == ")":
                        opened -= 1
                    self._advance()

                return Token(
                    self.stream,
                    start - 2,
                    self.n,
                    TokenType.Literal,
                    self.stream[start : self.n - 1].strip(),
                )
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
                        raise LexError(self.stream, start, self.n, "unfinished comment")
                    elif self.ch == "*":
                        self._advance()
                        if self.ch == "/":
                            self._advance()
                            break

                return None
            else:
                # just a division operator
                return Token(self.stream, self.n, 1, TokenType.Divide)
        elif self.ch == "<" and (template := self._try_read_template()):
            return Token(
                self.stream, self.n, self.n - prevn, TokenType.Template, template
            )
        elif self.ch in ("'", '"'):
            s = self._read_str()
            return Token(self.stream, self.n, len(s) + 2, TokenType.String, s)
        elif self.ch == "#":
            self._advance()
            if self.ch in ("'", '"'):
                s = self._read_str()
                if len(s) != 1:
                    raise LexError(
                        self.stream, start, self.n, "char literal is too long"
                    )
                return Token(self.stream, self.n, len(s) + 3, TokenType.Integer, ord(s))
            elif self.ch in string.ascii_letters or self.ch in string.digits:
                self._advance()
                assert self.ch_prev is not None
                return Token(
                    self.stream, self.n, 2, TokenType.Integer, ord(self.ch_prev)
                )
            else:
                raise LexError(self.stream, start, self.n, "invalid character literal")
        elif ttype := SIMPLE_TOKENS.get(self.ch):
            self._advance()
            if isinstance(ttype, dict):
                for target in ttype:
                    piece = self.stream[self.n : self.n + len(target) - 1]
                    if piece == target[1:]:
                        self._skip(len(target) - 1)
                        return Token(self.stream, self.n, len(target), ttype[target])

                return Token(self.stream, self.n, 1, TokenType.Unknown)
            else:
                return Token(self.stream, self.n, 1, ttype)
        elif self._isalpha():
            name = self._read_name()
            if name in RESERVED_WORDS:
                return Token(self.stream, self.n, len(name), TokenType.Reserved, name)
            else:
                return Token(self.stream, self.n, len(name), TokenType.Name, name)
        elif self._isnum():
            lhs, rhs = self._read_num()
            if isinstance(rhs, int):
                return Token(
                    self.stream, self.n, len(lhs), TokenType.Integer, (lhs, rhs)
                )
            else:
                return Token(
                    self.stream,
                    self.n,
                    len(lhs) + 1 + len(rhs),
                    TokenType.Float,
                    (lhs, rhs),
                )

        self._advance()
        return Token(self.stream, self.n, 1, TokenType.Unknown)

    def _read_name(self) -> str:
        start = self.n

        self._advance()
        while self._isalnum():
            self._advance()

        if self.ch is not None and not self._isspace() and self.ch not in SIMPLE_TOKENS:
            raise LexError(self.stream, start, self.n, "invalid word")

        return self.stream[start : self.n]

    def _read_num(self) -> Union[Tuple[str, int], Tuple[str, str]]:
        base = 10

        start = self.n
        self._advance()
        if self.ch_prev == "0":
            if self.ch == "x":
                self._advance()
                base = 16
            elif self.ch == "b":
                self._advance()
                base = 2
            elif self.ch == "o":
                self._advance()
                base = 8

        while self._isnum(base):
            self._advance()

        mid = self.n

        if base == 10 and self.ch == ".":
            self._advance()
            while self._isnum(base):
                self._advance()

        if self.ch is not None and not self._isspace() and self.ch not in SIMPLE_TOKENS:
            raise LexError(self.stream, start, self.n, "invalid number")

        if mid == self.n:
            return self.stream[start : self.n], base
        else:
            return self.stream[start:mid], self.stream[mid + 1 : self.n]

    def _read_str(self) -> str:
        start = self.n
        quote = self.ch

        self._advance()
        while self.ch is not None and self.ch != "\n" and self.ch != quote:
            self._advance()

        if self.ch is None or self.ch == "\n":
            raise LexError(self.stream, start, self.n - 1, "end of string not found")

        assert self.ch == quote
        self._advance()

        return self.stream[start + 1 : self.n - 1]

    def _try_read_template(self) -> Optional[Tuple[str, Optional[str]]]:
        state = (self.n, self.ch, self.ch_prev)
        try:
            if self.ch != "<":
                raise LexError(
                    self.stream, state[0], self.n, "start of template not found"
                )
            self._advance()

            name = self._read_name()
            while self._isspace() and self.ch != "\n":
                self._advance()

            if self.ch == ";":
                self._advance()
                start = self.n
                while self.ch is not None and self.ch != ">":
                    self._advance()
                if self.ch != ">":
                    raise LexError(self.stream, state[0], self.n, "unfinished template")

                self._advance()
                return (name, self.stream[start : self.n - 1].strip())
            elif self.ch == ">":
                self._advance()
                return (name, None)
            else:
                raise LexError(self.stream, state[0], self.n, "invalid template")
        except LexError:
            pass

        self.n, self.ch, self.ch_prev = state
        return None

    def _advance(self):
        self.ch_prev = self.ch

        self.n += 1
        if self.n >= len(self.stream):
            self.ch = None
        else:
            self.ch = self.stream[self.n]

    def _skip(self, n: int):
        self.n += n
        if self.n > len(self.stream):
            self.ch = None
            self.ch_prev = None
        elif self.n == len(self.stream):
            self.ch = None
            self.ch_prev = self.stream[-1]
        else:
            self.ch = self.stream[self.n]
            self.ch_prev = self.stream[self.n - 1]

    def _isspace(self):
        if self.ch is None:
            return False
        return self.ch in (" ", "\t", "\n")

    def _isalpha(self):
        if self.ch is None:
            return False
        return self.ch in ("_",) or "a" <= self.ch <= "z" or "A" <= self.ch <= "Z"

    def _isnum(self, base: int = 10):
        NUMBERS = "0123456789abcdef"
        if self.ch is None:
            return False
        return self.ch in NUMBERS[:base]

    def _isalnum(self):
        if self.ch is None:
            return False
        return (
            self.ch in ("_", "@")
            or "a" <= self.ch <= "z"
            or "A" <= self.ch <= "Z"
            or "0" <= self.ch <= "9"
        )
