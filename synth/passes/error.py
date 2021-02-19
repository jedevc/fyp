from ..error import ErrorLocation, SynthError
from ..node import Node


class ProcessingError(SynthError):
    """
    Indicates an error during later processing phases.
    """

    def __init__(self, node: Node, msg: str):
        super().__init__()

        start = node.token_start.position - node.token_start.length
        end = node.token_end.position - 1

        assert node.token_start.stream is node.token_end.stream

        self.location = ErrorLocation(start, end)
        self.msg = msg
        self.stream = node.token_start.stream

    def __str__(self) -> str:
        return "\n".join(
            [
                f"Processing error: {self.msg}",
                "",
                self.location.format(self.stream),
            ]
        )
