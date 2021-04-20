import re
from typing import Dict, Optional, Union

from ..builtins import functions, types, variables
from ..node import (
    LiteralExpressionNode,
    LiteralStatementNode,
    MapVisitor,
    TemplateValueNode,
    ValueNode,
)
from .error import ProcessingError


class TranslationTable:
    types = types.TRANSLATIONS
    variables = variables.TRANSLATIONS
    functions = functions.TRANSLATIONS


LIBS = {lib: __import__(lib) for lib in ("random", "string")}
TRANSLATIONS = {
    "table": TranslationTable,
}
EVAL_CONTEXT = {**LIBS, **TRANSLATIONS}


class TemplaterVisitor(MapVisitor):
    """
    Instantiate templates in place.
    """

    REF = re.compile(r"<\s*([^ ;]*)\s*>")
    ASSIGN = re.compile(r"<\s*([^ ;]*)\s*;(.*)>")

    def __init__(
        self, predefined: Optional[Dict[str, Union[str, int, float, bool]]] = None
    ):
        super().__init__()
        self.instantiations: Dict[str, Union[str, int, float, bool]] = predefined or {}

    def evaluate(self, name: str, definition: str) -> Union[str, bool, int, float]:
        # pylint: disable=eval-used
        result = eval(definition, EVAL_CONTEXT, self.instantiations)
        self.instantiations[name] = result
        return result

    def _expand(self, text: str) -> str:
        def expander(match: re.Match) -> str:
            groups = match.groups()
            if len(groups) == 1:
                name = groups[0]
                return str(self.instantiations[name])
            elif len(groups) == 2:
                name, definition = groups
                return str(self.evaluate(name, definition.strip()))
            else:
                raise RuntimeError()

        new = text
        new = TemplaterVisitor.REF.sub(expander, new)
        new = TemplaterVisitor.ASSIGN.sub(expander, new)
        return new

    def visit_value(self, node: ValueNode) -> ValueNode:
        if isinstance(node, TemplateValueNode):
            if node.definition:
                result = self.evaluate(node.name, node.definition)
            elif node.name in self.instantiations:
                result = self.instantiations[node.name]
            else:
                raise ProcessingError(
                    node, f"template for {node.name} has not been defined yet"
                )

            return node.construct(result)
        else:
            return super().visit_value(node)

    def visit_literal_expr(self, node: LiteralExpressionNode) -> LiteralExpressionNode:
        return LiteralExpressionNode(self._expand(node.content))

    def visit_literal_stmt(self, node: LiteralStatementNode) -> LiteralStatementNode:
        return LiteralStatementNode(self._expand(node.content))
