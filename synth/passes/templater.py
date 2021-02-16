from typing import Dict

from ..node import MapVisitor, TemplateValueNode, ValueNode
from .error import ProcessingError


class TemplaterVisitor(MapVisitor):
    """
    Instantiate templates in place.
    """

    def __init__(self):
        super().__init__()
        self.instantiations: Dict[str, str] = {}

    def _evaluator(self, definition: str) -> str:  # pylint: disable=unused-argument
        return "1"

    def visit_value(self, node: ValueNode) -> ValueNode:
        if isinstance(node, TemplateValueNode):
            if node.definition:
                result = self._evaluator(node.definition)
                self.instantiations[node.name] = result
            elif node.name in self.instantiations:
                result = self.instantiations[node.name]
            else:
                raise ProcessingError(
                    node, f"template for {node.name} has not been defined yet"
                )

            return TemplateValueNode.construct(result)
        else:
            return super().visit_value(node)
