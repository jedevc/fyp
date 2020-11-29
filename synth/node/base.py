from typing import Any


class Node:
    def __init__(self):
        self.token_start = None
        self.token_end = None

    def accept(self, visitor) -> Any:
        raise NotImplementedError()
