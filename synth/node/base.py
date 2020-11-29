from typing import TypeVar

from .visitor import Visitor

X = TypeVar("X")


class Node:
    def __init__(self):
        self.token_start = None
        self.token_end = None

    def accept(self, visitor: Visitor[X]) -> X:
        raise NotImplementedError()
