from ..builtins import functions, types, variables
from ..builtins.types import MetaType
from ..node import (
    ArrayNode,
    ArrayTypeNode,
    BinaryOperationNode,
    BlockNode,
    CallNode,
    DeclarationNode,
    DerefNode,
    FloatValueNode,
    FunctionNode,
    FuncTypeNode,
    IfNode,
    IntValueNode,
    LiteralNode,
    MetaTypeNode,
    PointerTypeNode,
    RefNode,
    SimpleTypeNode,
    SpecNode,
    SplitNode,
    StringValueNode,
    TraversalVisitor,
    TypeNode,
    UnknownTypeNode,
    ValueNode,
    VariableNode,
    WhileNode,
    type_check,
)
from .error import ProcessingError


class TypeCheckVisitor(TraversalVisitor[TypeNode]):
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

    def visit_type_simple(self, node: SimpleTypeNode) -> TypeNode:
        if node.core not in types.TRANSLATIONS:
            raise ProcessingError(node, f"{node.core} is not a valid type")

        return SimpleTypeNode(node.core)

    def visit_variable(self, node: VariableNode) -> TypeNode:
        if node.name in ("argc", "argv"):
            if self.block_current == "main":
                if self.block_seen_split:
                    raise ProcessingError(
                        node, f"variable {node.name} must appear before split"
                    )
            else:
                raise ProcessingError(
                    node, f"variable {node.name} cannot be referenced outside of main"
                )

            if node.name == "argc":
                return SimpleTypeNode("int")
            elif node.name == "argv":
                return ArrayTypeNode(PointerTypeNode(SimpleTypeNode("char")), None)
            else:
                raise RuntimeError()
        elif node.name in self.vars:
            return self.vars[node.name]
        elif node.name in variables.TRANSLATIONS or node.name in functions.TRANSLATIONS:
            # TODO: implement type derivations here
            raise NotImplementedError()
        else:
            raise ProcessingError(node, f"variable {node.name} does not exist")

    def visit_if(self, node: IfNode) -> None:
        condition_type = node.condition.accept(self)
        assert condition_type is not None
        if not type_check(MetaTypeNode(MetaType.Boolean), condition_type):
            raise ProcessingError(node.condition, "if condition must be bool")

        super().visit_if(node)

    def visit_while(self, node: WhileNode) -> None:
        condition_type = node.condition.accept(self)
        assert condition_type is not None
        if not type_check(MetaTypeNode(MetaType.Boolean), condition_type):
            raise ProcessingError(node.condition, "while condition must be bool")

        super().visit_while(node)

    def visit_ref(self, node: RefNode) -> TypeNode:
        tp = node.target.accept(self)
        assert tp is not None
        return PointerTypeNode(tp)

    def visit_deref(self, node: DerefNode) -> TypeNode:
        tp = node.target.accept(self)
        if isinstance(tp, PointerTypeNode):
            return tp.base
        else:
            raise ProcessingError(node, "cannot dereference non-pointer")

    def visit_function(self, node: FunctionNode) -> TypeNode:
        vtype = node.target.accept(self)
        if not isinstance(vtype, FuncTypeNode):
            raise ProcessingError(
                node, f"{node.target.name} exists, but is not a function"
            )

        if len(vtype.args) != len(node.arguments):
            raise ProcessingError(
                node,
                f"{node.target.name} expects {len(vtype.args)} arguments, but was given {len(node.arguments)}",
            )

        for i, arg in enumerate(node.arguments):
            type_result = arg.accept(self)
            assert type_result is not None
            if not type_check(vtype.args[i], type_result):
                # FIXME: better error message needed
                raise ProcessingError(arg, "argument type mismatch")

        return vtype.ret

    def visit_value(self, node: ValueNode) -> TypeNode:
        if isinstance(node, IntValueNode):
            return MetaTypeNode(MetaType.Integral)
        elif isinstance(node, FloatValueNode):
            return MetaTypeNode(MetaType.Floating)
        elif isinstance(node, StringValueNode):
            return PointerTypeNode(SimpleTypeNode("char"))
        else:
            raise RuntimeError()

    def visit_literal(self, node: LiteralNode) -> TypeNode:
        if node.content == "NULL":
            return PointerTypeNode(MetaTypeNode(MetaType.Void))
        else:
            return UnknownTypeNode()

    def visit_array(self, node: ArrayNode) -> TypeNode:
        index_type = node.index.accept(self)
        assert index_type is not None
        if not type_check(MetaTypeNode(MetaType.Integral), index_type):
            raise ProcessingError(
                node.index, "cannot index with non-integer expressions"
            )

        target_type = node.target.accept(self)
        if not isinstance(target_type, ArrayNode):
            raise ProcessingError(node.index, "cannot index non-array")

        return target_type

    def visit_binary(self, node: BinaryOperationNode) -> TypeNode:
        # TODO: this is very sloppy

        left_type = node.left.accept(self)
        right_type = node.right.accept(self)
        assert left_type is not None and right_type is not None

        if not type_check(left_type, right_type) and not type_check(
            right_type, left_type
        ):
            raise ProcessingError(node, "operands are not the same type")

        return MetaTypeNode(MetaType.Boolean)
