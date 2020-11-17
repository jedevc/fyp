import itertools

from .node import Node
from .token import Token


class LexError(BaseException):
    def __init__(self, start: int, end: int, msg: str):
        super().__init__()
        self.location = ErrorLocation(start, end)
        self.msg = msg

    def format(self, stream):
        return "\n".join(
            [
                f"Token error: {self.msg}",
                "",
                self.location.format(stream),
            ]
        )


class ParseError(BaseException):
    def __init__(self, token: Token, msg: str):
        super().__init__()
        self.location = ErrorLocation(token.position - token.length, token.position - 1)
        self.msg = msg

    def format(self, stream):
        return "\n".join(
            [
                f"Parse error: {self.msg}",
                "",
                self.location.format(stream),
            ]
        )


class ProcessingError(BaseException):
    def __init__(self, node: Node, msg: str):
        super().__init__()
        start = node.token_start.position - node.token_start.length
        end = node.token_end.position - 1
        self.location = ErrorLocation(start, end)
        self.msg = msg

    def format(self, stream):
        return "\n".join(
            [
                f"Processing error: {self.msg}",
                "",
                self.location.format(stream),
            ]
        )


class ErrorLocation:
    def __init__(self, start: int, end: int):
        assert start <= end
        self.start = start
        self.end = end

    def format(self, stream):
        # FIXME: we only *need* one iteration here
        start_line = 1
        start_column = 1
        for i in range(self.start):
            if stream[i] == "\n":
                start_column = 1
                start_line += 1
            else:
                start_column += 1
        end_line = 1
        end_column = 1
        for i in range(self.end):
            if stream[i] == "\n":
                end_column = 1
                end_line += 1
            else:
                end_column += 1

        lines = list(zip(itertools.count(), stream.split("\n")))

        CONTEXT = 3

        parts = []
        for i, line in lines[max(0, end_line - CONTEXT) : end_line]:
            prefix = f"  {str(i).rjust(6)}  |  "
            parts.append(f"{prefix}{line}")

        if start_line == end_line:
            parts.append(
                f"{len(prefix) * ' '}{(start_column - 1) * ' '}{(end_column - start_column) * '-'}^"
            )
        else:
            parts.append(f"{len(prefix) * ' '}{(end_column - 1) * '-'}^")
        return "\n".join(parts)
