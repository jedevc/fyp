from typing import Dict, Union

from ..node import MapVisitor, TemplateValueNode, ValueNode
from .error import ProcessingError

EVAL_CONTEXT = {lib: __import__(lib) for lib in ("random", "string")}


class TemplaterVisitor(MapVisitor):
    """
    Instantiate templates in place.
    """

    def __init__(self):
        super().__init__()
        self.instantiations: Dict[str, Union[str, int, float]] = {}

    def _evaluator(self, definition: str) -> Union[str, int, float]:
        # pylint: disable=eval-used
        result = eval(definition, EVAL_CONTEXT, self.instantiations)
        return result

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

            return node.construct(result)
        else:
            return super().visit_value(node)
