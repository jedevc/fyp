from ..builtins import functions, types, variables
from ..node import (
    BlockNode,
    CallNode,
    DeclarationNode,
    FunctionNode,
    FuncTypeNode,
    SimpleTypeNode,
    SpecNode,
    SplitNode,
    TraversalVisitor,
    VariableNode,
)
from .error import ProcessingError


class TypeCheckVisitor(TraversalVisitor):
    def __init__(self):
        super().__init__()
        self.vars = {}

        self.blocks = {}
        self.block_refs = {}

        self.block_current = None
        self.block_seen_split = False

    def visit_spec(self, node: SpecNode):
        # resolve block references after traversal
        super().visit_spec(node)

        if "main" not in self.blocks:
            raise ProcessingError(node, "no main block is defined")

        for block_name in self.block_refs:
            if block_name not in self.blocks:
                raise ProcessingError(
                    self.block_refs[block_name], f"block {block_name} is not defined"
                )

    def visit_block(self, node: BlockNode):
        self.block_current = node.name
        self.block_seen_split = False
        if self.block_current in self.blocks:
            raise ProcessingError(
                node, f"block {self.block_current} cannot be defined twice"
            )

        self.blocks[self.block_current] = node

        super().visit_block(node)

    def visit_split(self, node: SplitNode):
        self.block_seen_split = True

    def visit_call(self, node: CallNode):
        self.block_refs[node.target] = node

        super().visit_call(node)

    def visit_declaration(self, node: DeclarationNode):
        if node.name in self.vars:
            raise ProcessingError(
                node, f"variable {node.name} cannot be declared twice"
            )

        self.vars[node.name] = node.vartype

        super().visit_declaration(node)

    def visit_type_simple(self, node: SimpleTypeNode):
        if node.core not in types.TRANSLATIONS:
            raise ProcessingError(node, f"{node.core} is not a valid type")

    # def visit_type_pointer(self, node: PointerTypeNode):
    #     pass

    # def visit_type_array(self, node: ArrayTypeNode):
    #     pass

    # def visit_type_func(self, node: FuncTypeNode):
    #     pass

    def visit_variable(self, node: VariableNode):
        if node.name in ("argc", "argv"):
            if self.block_current == "main":
                if self.block_seen_split:
                    raise ProcessingError(
                        node, f"variable {node.name} must appear before split"
                    )
                else:
                    super().visit_variable(node)
            else:
                raise ProcessingError(
                    node, f"variable {node.name} cannot be referenced outside of main"
                )
        elif node.name in self.vars:
            super().visit_variable(node)
        elif node.name not in variables.TRANSLATIONS:
            super().visit_variable(node)
        else:
            raise ProcessingError(node, f"variable {node.name} does not exist")

    def visit_function(self, node: FunctionNode):
        if node.target not in self.vars and node.target not in functions.TRANSLATIONS:
            raise ProcessingError(node, f"function {node.target} does not exist")

        if node.target in self.vars and not isinstance(
            self.vars[node.target], FuncTypeNode
        ):
            raise ProcessingError(node, f"{node.target} exists, but is not a function")

        super().visit_function(node)
