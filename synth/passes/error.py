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
