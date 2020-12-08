from typing import Dict, List, Union

from ..block import (
    Array,
    Assignment,
    Block,
    Call,
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
)
from ..chunk import Chunk, ChunkSet
from ..node import (
    ArrayNode,
    AssignmentNode,
    BinaryOperationNode,
    BlockNode,
    CallNode,
    DerefNode,
    ExpressionStatementNode,
    FunctionNode,
    IfNode,
    RefNode,
    SpecNode,
    SplitNode,
    ValueNode,
    VariableNode,
    Visitor,
)
from .error import ProcessingError


class Splitter:
    pass


class BlockifyVisitor(Visitor[None]):
    def __init__(self, chunks: ChunkSet):
        super().__init__()
        self.chunks = chunks

        self.blocks: Dict[str, Block] = {}

    def result(self) -> List[Block]:
        return list(self.blocks.values())

    def visit_spec(self, node: SpecNode) -> None:
        self.blocks = {block.name: Block(block.name) for block in node.blocks}
        for block in node.blocks:
            block.accept(self)

    def visit_block(self, node: BlockNode) -> None:
        count = 1

        def name(n):
            if n == 1:
                return node.name
            else:
                return f"{node.name}{n}"

        for statement in node.statements:
            if isinstance(statement, SplitNode):
                # split off into new block
                next_block = Block(name(count + 1))
                caller = Call(next_block)
                self.blocks[name(count)].add_statement(caller)

                self.blocks[name(count + 1)] = next_block
                count += 1
            else:
                stmt = statement.accept(BlockifyStatementVisitor(self))
                self.blocks[name(count)].add_statement(stmt)

    def lookup_var(self, name: str) -> Chunk:
        chunk = self.chunks.find(name)
        if chunk is None:
            # internal error, we should have applied a type check pass before this
            raise RuntimeError("variable was not found")
        return chunk


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
        raise ProcessingError(node, "split is invalid here")

    def visit_if(self, node: IfNode) -> Statement:
        return If(
            node.condition.accept(BlockifyExpressionVisitor(self.parent)),
            [stmt.accept(self) for stmt in node.if_statements],
            [stmt.accept(self) for stmt in node.else_statements],
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
        return Variable(self.parent.lookup_var(node.name), node.name)

    def visit_deref(self, node: DerefNode) -> Lvalue:
        return Deref(node.target.accept(self))

    def visit_array(self, node: ArrayNode) -> Lvalue:
        return Array(
            node.target.accept(self),
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
        return Function(node.target, [expr.accept(self) for expr in node.arguments])

    def visit_value(self, node: ValueNode) -> Expression:
        return Value(node.value)

    def visit_binary(self, node: BinaryOperationNode) -> Expression:
        return Operation(node.op, node.left.accept(self), node.right.accept(self))
