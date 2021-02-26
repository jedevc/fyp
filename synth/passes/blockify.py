from typing import Dict, List, Optional, Tuple, Union

from ..builtins import functions, variables
from ..graph import (
    Array,
    Assignment,
    Block,
    Call,
    Cast,
    Chunk,
    ChunkVariable,
    Deref,
    Expression,
    ExpressionStatement,
    Function,
    If,
    Lvalue,
    Operation,
    Ref,
    Statement,
    Value,
    Variable,
    While,
)
from ..node import (
    ArrayNode,
    AssignmentNode,
    BinaryOperationNode,
    BlockNode,
    BoolValueNode,
    CallNode,
    CastNode,
    DerefNode,
    ExpressionStatementNode,
    FloatValueNode,
    FunctionNode,
    IfNode,
    IntValueNode,
    LiteralNode,
    RefNode,
    SpecNode,
    SplitNode,
    StatementNode,
    StringValueNode,
    ValueNode,
    VariableNode,
    Visitor,
    WhileNode,
)
from ..utils import generate_unique_name
from .error import ProcessingError


class BlockifyVisitor(Visitor[None]):
    def __init__(self, chunks: List[Chunk], extern: Chunk):
        super().__init__()
        self.chunks = chunks
        self.extern = extern

        self.blocks: Dict[str, Block] = {}

    def result(self) -> List[Block]:
        return list(self.blocks.values())

    def visit_spec(self, node: SpecNode):
        self.blocks = {block.name: Block(block.name) for block in node.blocks}
        for block in node.blocks:
            block.accept(self)

    def visit_block(self, node: BlockNode):
        statements = self.process_statements(node.statements)
        self.blocks[node.name].add_statements(statements)

    def process_statements(self, statements: List[StatementNode]) -> List[Statement]:
        name = None
        result_statements: List[Statement] = []

        for statement in statements:
            if isinstance(statement, SplitNode):
                name = generate_unique_name(8)

                next_block = Block(name)
                self.blocks[name] = next_block

                caller = Call(next_block)
                result_statements.append(caller)
            elif name is not None:
                stmt = statement.accept(BlockifyStatementVisitor(self))
                self.blocks[name].add_statement(stmt)
            else:
                stmt = statement.accept(BlockifyStatementVisitor(self))
                result_statements.append(stmt)

        return result_statements

    def lookup_var(self, name: str) -> ChunkVariable:
        if name in ("argc", "argv"):
            return ChunkVariable(name, None, None)
        elif name in variables.TYPES:
            return ChunkVariable(name, None, None)
        elif name in functions.SIGNATURES:
            return ChunkVariable(name, None, None)
        elif (var := self.extern.lookup(name)) :
            return var
        else:
            for chunk in self.chunks:
                if (var := chunk.lookup(name)) :
                    return var

            raise KeyError(f"variable {name} not found")


class BlockifyStatementVisitor(Visitor[Union[Statement]]):
    def __init__(self, parent: BlockifyVisitor):
        super().__init__()
        self.parent = parent

    def visit_assignment(self, node: AssignmentNode) -> Statement:
        return Assignment(
            node.target.accept(BlockifyLvalueVisitor(self.parent)),
            node.expression.accept(BlockifyExpressionVisitor(self.parent)),
        )

    def visit_call(self, node: CallNode) -> Statement:
        return Call(self.parent.blocks[node.target])

    def visit_split(self, node: SplitNode) -> Statement:
        raise RuntimeError("split should never be manually visited")

    def visit_if(self, node: IfNode) -> Statement:
        groups: List[Tuple[Optional[Expression], List[Statement]]] = []

        nodeiter: Optional[IfNode] = node
        while nodeiter is not None:
            groups.append(
                (
                    nodeiter.condition.accept(BlockifyExpressionVisitor(self.parent)),
                    self.parent.process_statements(nodeiter.statements),
                )
            )
            if nodeiter.else_statements:
                groups.append(
                    (None, self.parent.process_statements(nodeiter.else_statements))
                )
            nodeiter = nodeiter.else_if

        return If(groups)

    def visit_while(self, node: WhileNode) -> Statement:
        return While(
            node.condition.accept(BlockifyExpressionVisitor(self.parent)),
            self.parent.process_statements(node.statements),
        )

    def visit_exprstmt(self, node: ExpressionStatementNode) -> Statement:
        return ExpressionStatement(
            node.expression.accept(BlockifyExpressionVisitor(self.parent))
        )


class BlockifyLvalueVisitor(Visitor[Lvalue]):
    def __init__(self, parent: BlockifyVisitor):
        super().__init__()
        self.parent = parent

    def visit_variable(self, node: VariableNode) -> Lvalue:
        try:
            var = self.parent.lookup_var(node.name)
            return Variable(var)
        except KeyError as e:
            raise ProcessingError(node, e.args[0])

    def visit_deref(self, node: DerefNode) -> Lvalue:
        return Deref(node.target.accept(BlockifyExpressionVisitor(self.parent)))

    def visit_array(self, node: ArrayNode) -> Lvalue:
        return Array(
            node.target.accept(BlockifyExpressionVisitor(self.parent)),
            node.index.accept(BlockifyExpressionVisitor(self.parent)),
        )


class BlockifyExpressionVisitor(Visitor[Expression]):
    def __init__(self, parent: BlockifyVisitor):
        super().__init__()
        self.parent = parent

    def visit_array(self, node: ArrayNode) -> Expression:
        return node.accept(BlockifyLvalueVisitor(self.parent))

    def visit_variable(self, node: VariableNode) -> Expression:
        return node.accept(BlockifyLvalueVisitor(self.parent))

    def visit_deref(self, node: DerefNode) -> Expression:
        return node.accept(BlockifyLvalueVisitor(self.parent))

    def visit_ref(self, node: RefNode) -> Expression:
        return Ref(node.target.accept(BlockifyLvalueVisitor(self.parent)))

    def visit_function(self, node: FunctionNode) -> Expression:
        var = node.target.accept(BlockifyLvalueVisitor(self.parent))
        return Function(var, [expr.accept(self) for expr in node.arguments])

    def visit_value(self, node: ValueNode) -> Expression:
        if isinstance(node, StringValueNode):
            return Value('"' + node.value + '"')
        elif isinstance(node, IntValueNode):
            if node.base == 2:
                return Value(bin(node.value))
            elif node.base == 8:
                return Value(oct(node.value))
            elif node.base == 10:
                return Value(str(node.value))
            elif node.base == 16:
                return Value(hex(node.value))
            else:
                raise RuntimeError("value unrepresentable in C")
        elif isinstance(node, FloatValueNode):
            return Value(f"{node.left}.{node.right}")
        elif isinstance(node, BoolValueNode):
            if node.value:
                return Value("true")
            else:
                return Value("false")
        else:
            raise RuntimeError()

    def visit_cast(self, node: CastNode) -> Expression:
        return Cast(node.expr.accept(self), node.cast)

    def visit_literal(self, node: LiteralNode) -> Expression:
        return Value(node.content.rstrip(";"))

    def visit_binary(self, node: BinaryOperationNode) -> Expression:
        return Operation(node.op, node.left.accept(self), node.right.accept(self))
