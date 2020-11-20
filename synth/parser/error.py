from .node import Node
from .token import Token


class SynthError(BaseException):
    def format(self, stream: str):
        raise NotImplementedError()


class LexError(SynthError):
    """
    Indicates an error during tokenisation.
    """

    def __init__(self, start: int, end: int, msg: str):
        super().__init__()
        self.location = ErrorLocation(start, end)
        self.msg = msg

    def format(self, stream: str):
        return "\n".join(
            [
                f"Token error: {self.msg}",
                "",
                self.location.format(stream),
            ]
        )


class ParseError(SynthError):
    """
    Indicates an error during parsing.
    """

    def __init__(self, token: Token, msg: str):
        super().__init__()
        self.location = ErrorLocation(token.position - token.length, token.position - 1)
        self.msg = msg

    def format(self, stream: str):
        return "\n".join(
            [
                f"Parse error: {self.msg}",
                "",
                self.location.format(stream),
            ]
        )


class ProcessingError(SynthError):
    """
    Indicates an error during later processing phases.
    """

    def __init__(self, node: Node, msg: str):
        super().__init__()
        start = node.token_start.position - node.token_start.length
        end = node.token_end.position - 1
        self.location = ErrorLocation(start, end)
        self.msg = msg

    def format(self, stream: str):
        return "\n".join(
            [
                f"Processing error: {self.msg}",
                "",
                self.location.format(stream),
            ]
        )


class ErrorLocation:
    """
    Utility class to represent the location of an error.

    Additionally, it provides a sophisticated formatting method for neatly
    formatting errors.
    """

    def __init__(self, start: int, end: int):
        assert start <= end
        self.start = start
        self.end = end

    def format(self, stream: str):
        """
        Format a nice printout for the error location given the original
        stream used to parse everything.
        """

        # track line-column positions of the token
        start_line = 1
        start_column = 1
        end_line = 1
        end_column = 1

        # track lines
        count = 1
        pos = 0

        lines = []
        i = 0
        for i, ch in enumerate(stream):
            if ch == "\n":
                lines.append((count, stream[pos:i]))
                pos = i + 1
                count += 1

                if i < self.end:
                    end_column = 1
                    end_line += 1
                if i < self.start:
                    start_column = 1
                    start_line += 1
            else:
                if i < self.end:
                    end_column += 1
                if i < self.start:
                    start_column += 1
        if pos != 0:
            # left-over data
            lines.append((count, stream[pos:i]))

        parts = []
        CONTEXT = 2

        # before context
        before_ctx = max(0, end_line - CONTEXT - 1)
        for i, line in lines[before_ctx:end_line]:
            prefix = f"  {str(i).rjust(6)}  |  "
            parts.append(f"{prefix}{line}")

        # indicator
        if start_line == end_line:
            parts.append(
                f"{len(prefix) * ' '}{(start_column - 1) * ' '}{(end_column - start_column) * '-'}^"
            )
        else:
            parts.append(f"{len(prefix) * ' '}{(end_column - 1) * '-'}^")

        # after context
        after_ctx = end_line + CONTEXT
        for i, line in lines[end_line:after_ctx]:
            prefix = f"  {str(i).rjust(6)}  |  "
            parts.append(f"{prefix}{line}")

        return "\n".join(parts)
