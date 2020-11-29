from typing import Any

from .visitor import Visitor


class Node:
    def __init__(self):
        self.token_start = None
        self.token_end = None

    def accept(self, visitor: Visitor) -> Any:
        raise NotImplementedError()
