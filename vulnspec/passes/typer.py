import functools
from typing import Dict, Optional

from ..builtins import MetaTypes, functions, types, variables
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
    LiteralExpressionNode,
    MetaTypeNode,
    PointerTypeNode,
    RefNode,
    SimpleTypeNode,
    SizeOfNode,
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


@functools.lru_cache(maxsize=None)
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

        self.block_current: Optional[str] = None
        self.block_seen_split = False

    def visit_spec(self, node: SpecNode):
        for block in node.blocks:
            if block.name in self.blocks:
                raise ProcessingError(
                    block, f"block {block.name} cannot be defined twice"
                )

            self.blocks[block.name] = block

        if self.require_main and "main" not in self.blocks:
            raise ProcessingError(node, "no main block is defined")

        super().visit_spec(node)

    def visit_block(self, node: BlockNode):
        self.block_current = node.name
        self.block_seen_split = False
        if self.block_current in self.vars:
            raise ProcessingError(
                node,
                f"name {node.name} has already been used as a variable",
            )

        self.blocks[self.block_current] = node

        super().visit_block(node)

    def visit_split(self, node: SplitNode):
        self.block_seen_split = True

    def visit_call(self, node: CallNode):
        if node.target not in self.blocks:
            raise ProcessingError(node, f"block {node.target} is not defined")

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
        elif node.name in self.blocks:
            if "func" in self.blocks[node.name].constraints:
                return FuncTypeNode(SimpleTypeNode("void"), [])
            else:
                raise ProcessingError(
                    node,
                    "blocks can only be referenced as variables when constrained as functions",
                )
        else:
            raise ProcessingError(node, f"variable {node.name} does not exist")

    def visit_if(self, node: IfNode) -> None:
        condition_type = node.condition.accept(self)
        assert condition_type is not None
        if not type_check(MetaTypeNode(MetaTypes.Boolean), condition_type):
            raise ProcessingError(node.condition, "if condition must be bool")

        super().visit_if(node)

    def visit_while(self, node: WhileNode) -> None:
        condition_type = node.condition.accept(self)
        assert condition_type is not None
        if not type_check(MetaTypeNode(MetaTypes.Boolean), condition_type):
            raise ProcessingError(node.condition, "while condition must be bool")

        super().visit_while(node)

    def visit_assignment(self, node: AssignmentNode) -> None:
        lhs_type = node.target.accept(self)
        rhs_type = node.expression.accept(self)
        assert lhs_type is not None and rhs_type is not None

        if isinstance(lhs_type, FuncTypeNode):
            raise ProcessingError(node.target, "cannot assign to function")
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
        if not isinstance(vtype, FuncTypeNode):
            raise ProcessingError(node, "value is not a function and cannot be called")

        if not vtype.variadic and len(vtype.args) != len(node.arguments):
            funcname = (
                node.target.name
                if isinstance(node.target, VariableNode)
                else "function"
            )
            raise ProcessingError(
                node,
                f"{funcname} expects {len(vtype.args)} arguments, but was given {len(node.arguments)}",
            )

        for arg, varg in zip(node.arguments, vtype.args):
            if isinstance(arg, FuncTypeNode):
                raise ProcessingError(arg, "cannot pass function to function")

            type_result = arg.accept(self)
            assert type_result is not None
            if not type_check(varg, type_result):
                # FIXME: better error message needed
                raise ProcessingError(arg, "argument type mismatch")

        if vtype.variadic:
            for arg in node.arguments[len(vtype.args) :]:
                arg.accept(self)

        return vtype.ret

    def visit_value(self, node: ValueNode) -> TypeNode:
        if isinstance(node, IntValueNode):
            return MetaTypeNode(MetaTypes.Integral)
        elif isinstance(node, FloatValueNode):
            return MetaTypeNode(MetaTypes.Floating)
        elif isinstance(node, BoolValueNode):
            return MetaTypeNode(MetaTypes.Boolean)
        elif isinstance(node, StringValueNode):
            return PointerTypeNode(SimpleTypeNode("char"))
        else:
            raise RuntimeError()

    def visit_sizeof(self, node: SizeOfNode) -> TypeNode:
        node.tp.accept(self)
        return MetaTypeNode(MetaTypes.Integral)

    def visit_cast(self, node: CastNode) -> TypeNode:
        return node.cast

    def visit_literal_expr(self, node: LiteralExpressionNode) -> TypeNode:
        if node.content == "NULL":
            return MetaTypeNode(MetaTypes.Pointer)
        else:
            return MetaTypeNode(MetaTypes.Any)

    def visit_array(self, node: ArrayNode) -> TypeNode:
        index_type = node.index.accept(self)
        assert index_type is not None
        if not type_check(MetaTypeNode(MetaTypes.Integral), index_type):
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
            bool_type = MetaTypeNode(MetaTypes.Boolean)
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
            bool_type = MetaTypeNode(MetaTypes.Boolean)
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
            return MetaTypeNode(MetaTypes.Boolean)
        elif node.op in ARITHMETIC_OPERATORS:
            if not type_check(left_type, right_type) and not type_check(
                right_type, left_type
            ):
                raise ProcessingError(node, "operands are not the same type")
            return left_type
        else:
            raise RuntimeError()
