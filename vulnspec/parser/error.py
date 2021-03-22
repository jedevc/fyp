from ..common.error import ErrorLocation, SynthError
from .token import Token


class LexError(SynthError):
    """
    Indicates an error during tokenisation.
    """

    def __init__(self, stream: str, start: int, end: int, msg: str):
        super().__init__()
        self.stream = stream
        self.location = ErrorLocation(start, end)
        self.msg = msg

    def __str__(self) -> str:
        return "\n".join(
            [
                f"Token error: {self.msg}",
                "",
                self.location.format(self.stream),
            ]
        )


class ParseError(SynthError):
    """
    Indicates an error during parsing.
    """

    def __init__(self, token: Token, msg: str):
        super().__init__()
        self.stream = token.stream
        self.location = ErrorLocation(token.position - token.length, token.position - 1)
        self.msg = msg

    def __str__(self) -> str:
        return "\n".join(
            [
                f"Parse error: {self.msg}",
                "",
                self.location.format(self.stream),
            ]
        )
