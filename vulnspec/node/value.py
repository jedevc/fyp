import json
from typing import Optional, Union

from .base import Node, X
from .visitor import Visitor


class ValueNode(Node):
    def accept(self, visitor: Visitor[X]) -> X:
        return visitor.visit_value(self)


class IntValueNode(ValueNode):
    def __init__(self, value: int, base: int):
        super().__init__()
        self.value = value
        self.base = base

    def __str__(self) -> str:
        return str(self.value)


class FloatValueNode(ValueNode):
    def __init__(self, left: int, right: int):
        super().__init__()
        self.left = left
        self.right = right

    def __str__(self) -> str:
        return f"{self.left}.{self.right}"


class BoolValueNode(ValueNode):
    def __init__(self, value: bool):
        super().__init__()
        self.value = value

    def __str__(self) -> str:
        if self.value:
            return "true"
        else:
            return "false"


class StringValueNode(ValueNode):
    def __init__(self, value: str):
        super().__init__()
        self.value = value

    def __str__(self) -> str:
        return json.dumps(self.value)


class TemplateValueNode(ValueNode):
    def __init__(self, name: str, definition: Optional[str]):
        super().__init__()
        self.name = name
        self.definition = definition

    def construct(self, source: Union[str, bool, int, float]) -> ValueNode:
        node: ValueNode
        if isinstance(source, str):
            node = StringValueNode(source)
        elif isinstance(source, bool):
            node = BoolValueNode(source)
        elif isinstance(source, int):
            node = IntValueNode(source, 10)
        elif isinstance(source, float):
            lhs, rhs = f"{source:.20f}".split(".")
            node = FloatValueNode(int(lhs), int(rhs))
        else:
            raise TypeError(f"cannot construct value from {type(source)}")

        node.token_start = self.token_start
        node.token_end = self.token_end

        return node

    def __str__(self) -> str:
        return f"<{self.name}; {self.definition}>"
