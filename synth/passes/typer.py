import functools
from typing import Dict, Optional

from ..builtins import functions, types, variables
from ..builtins.types import MetaType
from ..node import (
    ARITHMETIC_OPERATORS,
    BOOLEAN_OPERATORS,
    COMPARISON_OPERATORS,
    ArrayNode,
    ArrayTypeNode,
    AssignmentNode,
    BinaryOperationNode,
    BlockNode,
    BoolValueNode,
    CallNode,
    CastNode,
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
    UnaryOperationNode,
    ValueNode,
    VariableNode,
    WhileNode,
    type_check,
)
from ..parser import Lexer, Parser
from .error import ProcessingError


@functools.cache
def parse_typestring(typestr: str) -> TypeNode:
    lex = Lexer(typestr)
    tokens = lex.tokens_list()

    parser = Parser(tokens)
    parser.advance()
    tp = parser.declaration_type()
    return tp


class TypeCheckVisitor(TraversalVisitor[TypeNode]):
    def __init__(self, require_main: bool = True):
        super().__init__()
        self.require_main = require_main

        self.vars: Dict[str, TypeNode] = {}

        self.blocks: Dict[str, BlockNode] = {}
        self.block_refs: Dict[str, CallNode] = {}

        self.block_current: Optional[str] = None
        self.block_seen_split = False

    def visit_spec(self, node: SpecNode):
        # resolve block references after traversal
        super().visit_spec(node)

        if self.require_main and "main" not in self.blocks:
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
        if node.name in ("argc", "argv"):
            raise ProcessingError(
                node,
                f"variable {node.name} has already been implicitly declared by main",
            )
        elif node.name in self.vars:
            raise ProcessingError(
                node, f"variable {node.name} has already been declared"
            )
        elif node.name in variables.TYPES:
            raise ProcessingError(
                node,
                f"variable {node.name} has already been declared as a builtin variable",
            )
        elif node.name in functions.SIGNATURES:
            raise ProcessingError(
                node,
                f"variable {node.name} has already been declared as a builtin function",
            )

        self.vars[node.name] = node.vartype
        if node.initial:
            rhs_type = node.initial.accept(self)
            assert rhs_type is not None

            if not type_check(self.vars[node.name], rhs_type):
                raise ProcessingError(
                    node, "incompatible types in declaration assignment"
                )

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
        elif node.name in variables.TYPES:
            return parse_typestring(variables.TYPES[node.name])
        elif node.name in functions.SIGNATURES:
            return parse_typestring(functions.SIGNATURES[node.name])
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

    def visit_assignment(self, node: AssignmentNode) -> None:
        lhs_type = node.target.accept(self)
        rhs_type = node.expression.accept(self)
        assert lhs_type is not None and rhs_type is not None

        if not type_check(lhs_type, rhs_type):
            raise ProcessingError(node, "incompatible types in assignment")

        super().visit_assignment(node)

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
        funcname = (
            node.target.name if isinstance(node.target, VariableNode) else "function"
        )
        if not isinstance(vtype, FuncTypeNode):
            raise ProcessingError(node, f"{funcname} exists, but is not a function")

        if not vtype.variadic and len(vtype.args) != len(node.arguments):
            raise ProcessingError(
                node,
                f"{funcname} expects {len(vtype.args)} arguments, but was given {len(node.arguments)}",
            )

        for arg, varg in zip(node.arguments, vtype.args):
            type_result = arg.accept(self)
            assert type_result is not None
            if not type_check(varg, type_result):
                # FIXME: better error message needed
                raise ProcessingError(arg, "argument type mismatch")

        return vtype.ret

    def visit_value(self, node: ValueNode) -> TypeNode:
        if isinstance(node, IntValueNode):
            return MetaTypeNode(MetaType.Integral)
        elif isinstance(node, FloatValueNode):
            return MetaTypeNode(MetaType.Floating)
        elif isinstance(node, BoolValueNode):
            return MetaTypeNode(MetaType.Boolean)
        elif isinstance(node, StringValueNode):
            return PointerTypeNode(SimpleTypeNode("char"))
        else:
            raise RuntimeError()

    def visit_cast(self, node: CastNode) -> TypeNode:
        return node.cast

    def visit_literal(self, node: LiteralNode) -> TypeNode:
        if node.content == "NULL":
            return MetaTypeNode(MetaType.Integral)
        else:
            return MetaTypeNode(MetaType.Any)

    def visit_array(self, node: ArrayNode) -> TypeNode:
        index_type = node.index.accept(self)
        assert index_type is not None
        if not type_check(MetaTypeNode(MetaType.Integral), index_type):
            raise ProcessingError(
                node.index, "cannot index with non-integer expressions"
            )

        target_type = node.target.accept(self)
        if not isinstance(target_type, ArrayTypeNode) and not isinstance(
            target_type, PointerTypeNode
        ):
            raise ProcessingError(node.index, "cannot index non-array")

        return target_type.base

    def visit_unary(self, node: UnaryOperationNode) -> TypeNode:
        item_type = node.item.accept(self)
        assert item_type is not None

        if node.op in BOOLEAN_OPERATORS:
            bool_type = MetaTypeNode(MetaType.Boolean)
            if not type_check(bool_type, item_type):
                raise ProcessingError(node.item, "operand should be boolean")
            return bool_type
        elif node.op in ARITHMETIC_OPERATORS:
            return item_type
        else:
            raise RuntimeError()

    def visit_binary(self, node: BinaryOperationNode) -> TypeNode:
        left_type = node.left.accept(self)
        right_type = node.right.accept(self)
        assert left_type is not None and right_type is not None

        if node.op in BOOLEAN_OPERATORS:
            bool_type = MetaTypeNode(MetaType.Boolean)
            if not type_check(bool_type, left_type):
                raise ProcessingError(node.left, "left operand should be boolean")
            if not type_check(bool_type, right_type):
                raise ProcessingError(node.left, "right operand should be boolean")
            return bool_type
        elif node.op in COMPARISON_OPERATORS:
            if not type_check(left_type, right_type) and not type_check(
                right_type, left_type
            ):
                raise ProcessingError(node, "operands are not the same type")
            return MetaTypeNode(MetaType.Boolean)
        elif node.op in ARITHMETIC_OPERATORS:
            if not type_check(left_type, right_type) and not type_check(
                right_type, left_type
            ):
                raise ProcessingError(node, "operands are not the same type")
            return left_type
        else:
            raise RuntimeError()
