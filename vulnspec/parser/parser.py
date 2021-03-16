from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from ..node import (
    ArrayNode,
    ArrayTypeNode,
    AssignmentNode,
    BinaryOperationNode,
    BlockNode,
    BoolValueNode,
    CallNode,
    CastNode,
    ChunkNode,
    DeclarationNode,
    DerefNode,
    ExpressionNode,
    ExpressionStatementNode,
    ExternChunkNode,
    FloatValueNode,
    FunctionNode,
    FuncTypeNode,
    IfNode,
    IntValueNode,
    LiteralNode,
    LvalueNode,
    Node,
    Operator,
    PointerTypeNode,
    RefNode,
    SimpleTypeNode,
    SpecNode,
    SplitNode,
    StatementNode,
    StringValueNode,
    TemplateValueNode,
    TypeNode,
    UnaryOperationNode,
    VariableNode,
    WhileNode,
)
from .error import ParseError
from .token import PRINTABLE_NAMES, ReservedWord, Token, TokenType

N = TypeVar("N", bound=Node)


class Parser:
    """
    Producer for an Abstract Syntax Tree given a valid well-structured series
    of tokens.
    """

    def __init__(self, tokens: List[Token]):
        assert len(tokens) >= 0

        self.pos = -1
        self.tokens = tokens

        self.current: Optional[Token] = None
        self.last: Optional[Token] = None

        self.starts: List[int] = []

    def parse(self) -> Node:
        """
        Perform the main parse operation.

        This is the only method that should be externally invoked by the
        caller on this object.
        """

        self.advance()

        return self.spec()

    def spec(self) -> SpecNode:
        """
        Parse the entire specification.
        """

        self.node_enter()

        chunks = []
        blocks = []
        while self.pos < len(self.tokens):
            if self.accept(TokenType.EOF):
                break
            elif self.accept(TokenType.Newline):
                continue

            assert self.current is not None
            if self.current.ttype != TokenType.Reserved:
                raise ParseError(self.current, "expected opening statement")

            if self.current.lexeme == ReservedWord.Chunk:
                chunks.append(self.chunk())
            elif self.current.lexeme == ReservedWord.Extern:
                chunks.append(self.extern_chunk())
            elif self.current.lexeme == ReservedWord.Block:
                blocks.append(self.block())
            else:
                raise ParseError(self.current, "unknown statement type")

        return self.node_exit(SpecNode(chunks, blocks))

    def chunk(self) -> ChunkNode:
        """
        Parse a chunk of variables.
        """

        self.node_enter()

        self.expect(TokenType.Reserved, ReservedWord.Chunk)

        constraints = self.constraints()
        self.accept(TokenType.Newline)

        variables = [self.declaration()]
        while self.accept(TokenType.Comma):
            self.accept(TokenType.Newline)
            variables.append(self.declaration())
        self.end_of_line(after="chunk")

        return self.node_exit(ChunkNode(variables, constraints))

    def extern_chunk(self) -> ExternChunkNode:
        """
        Parse a chunk of extern variables.
        """

        self.node_enter()

        self.expect(TokenType.Reserved, ReservedWord.Extern)
        variables = [self.declaration()]
        while self.accept(TokenType.Comma):
            self.accept(TokenType.Newline)
            variables.append(self.declaration())
        self.end_of_line(after="extern")

        return self.node_exit(ExternChunkNode(variables))

    def block(self) -> BlockNode:
        """
        Parse a block of statements.
        """

        self.node_enter()

        self.expect(TokenType.Reserved, ReservedWord.Block)

        constraints = self.constraints()

        block_name = self.expect(TokenType.Name).lexeme
        statements = self.scope()

        return self.node_exit(BlockNode(block_name, statements, constraints))

    def constraints(self) -> List[str]:
        constraints = []
        if self.accept(TokenType.ParenOpen):
            while True:
                constraint = self.expect(TokenType.Name)
                constraints.append(constraint.lexeme)
                if not self.accept(TokenType.Comma):
                    break

            self.expect(TokenType.ParenClose)

        return constraints

    def statement(self) -> StatementNode:
        """
        Parse a single statement.
        """

        self.node_enter()

        stmt: StatementNode
        if self.accept(TokenType.Ellipsis):
            stmt = self.node_exit(SplitNode())
            self.end_of_line(after="splitter")
        elif self.accept(TokenType.Reserved, ReservedWord.Call):
            target = self.expect(TokenType.Name)
            stmt = self.node_exit(CallNode(target.lexeme))
            self.end_of_line(after="call")
        elif self.accept(TokenType.Reserved, ReservedWord.While):
            condition = self.expression()
            statements = self.scope()
            stmt = self.node_exit(WhileNode(condition, statements))
            self.end_of_line(after="while")
        elif self.accept(TokenType.Reserved, ReservedWord.If):
            condition = self.expression()
            statements = self.scope()
            else_action: Optional[Union[IfNode, List[StatementNode]]] = None
            if self.accept(TokenType.Reserved, ReservedWord.Else):
                if self.match(TokenType.Reserved, ReservedWord.If):
                    # read another If
                    stmt = self.statement()
                    assert isinstance(stmt, IfNode)
                    else_action = stmt
                else:
                    else_action = self.scope()
                    self.end_of_line(after="else")
            else:
                else_action = None
                self.end_of_line(after="if")

            stmt = self.node_exit(IfNode(condition, statements, else_action))
        else:
            state = (self.pos, self.current, self.last)
            try:
                lvalue = self.lvalue()
                self.expect(TokenType.Assign)
                exp = self.expression()
                stmt = self.node_exit(AssignmentNode(lvalue, exp))
                self.end_of_line(after="assignment")
            except ParseError:
                self.pos, self.current, self.last = state

                self.node_cancel()
                stmt = ExpressionStatementNode(self.expression())
                self.end_of_line(after="expression statement")

        return stmt

    def scope(self) -> List[StatementNode]:
        self.expect(TokenType.BraceOpen)
        self.accept(TokenType.Newline)
        statements = []
        while not self.accept(TokenType.BraceClose):
            statements.append(self.statement())
        return statements

    def expression(self) -> ExpressionNode:
        """
        Parse an expression.
        """

        return self.disjunction()

    def disjunction(self) -> ExpressionNode:
        """
        Parse a boolean disjunction.
        """

        return self.binary(
            self.conjunction, self.conjunction, {TokenType.BooleanOr: Operator.Or}
        )

    def conjunction(self) -> ExpressionNode:
        """
        Parse a boolean conjunction.
        """

        return self.binary(
            self.comparison, self.comparison, {TokenType.BooleanAnd: Operator.And}
        )

    def comparison(self) -> ExpressionNode:
        """
        Parse a comparison.
        """

        return self.binary(
            self.sum,
            self.sum,
            {
                TokenType.CompareNE: Operator.Neq,
                TokenType.CompareEQ: Operator.Eq,
                TokenType.CompareLT: Operator.Lt,
                TokenType.CompareLE: Operator.Lte,
                TokenType.CompareGT: Operator.Gt,
                TokenType.CompareGE: Operator.Gte,
            },
        )

    def sum(self) -> ExpressionNode:
        """
        Parse a sum.
        """

        return self.binary(
            self.product,
            self.sum,
            {
                TokenType.Plus: Operator.Add,
                TokenType.Minus: Operator.Subtract,
            },
        )

    def product(self) -> ExpressionNode:
        """
        Parse a product.
        """

        return self.binary(
            self.standalone,
            self.product,
            {
                TokenType.Times: Operator.Multiply,
                TokenType.Divide: Operator.Divide,
            },
        )

    def standalone(self) -> ExpressionNode:
        """
        Parse a standalone expression with a possible unary prefix operator.
        """

        return self.unary(
            self.atom,
            {
                TokenType.BooleanNot: Operator.Not,
                TokenType.Minus: Operator.Negate,
            },
        )

    def unary(
        self,
        item: Callable[[], ExpressionNode],
        operators: Dict[TokenType, Operator],
    ) -> ExpressionNode:
        """
        Parse an arbitrary unary expression.
        """

        self.node_enter()
        found = None
        for op in operators:
            if self.accept(op):
                found = op
                break

        operand = item()
        if found:
            return self.node_exit(UnaryOperationNode(operators[found], operand))
        else:
            self.node_cancel()
            return operand

    def binary(
        self,
        left: Callable[[], ExpressionNode],
        right: Callable[[], ExpressionNode],
        operators: Dict[TokenType, Operator],
    ) -> ExpressionNode:
        """
        Parse an arbitrary binary expression.
        """

        self.node_enter()
        op1 = left()
        for op in operators:
            if self.accept(op):
                op2 = right()
                return self.node_exit(BinaryOperationNode(operators[op], op1, op2))
        self.node_cancel()
        return op1

    def atom(self) -> ExpressionNode:
        """
        Parse an atomic expression.
        """

        self.node_enter()

        node: ExpressionNode
        if self.match(TokenType.ParenOpen):
            self.node_cancel()

            state = (self.pos, self.current, self.last)
            try:
                # we try this way first, since lvalues may use parenthesis to
                # parse more complex array indexing
                node = self.lvalue()
            except ParseError:
                self.pos, self.current, self.last = state
                self.expect(TokenType.ParenOpen)
                node = self.expression()
                self.expect(TokenType.ParenClose)
        elif self.accept(TokenType.BitwiseAnd):
            target = self.lvalue()
            node = self.node_exit(RefNode(target))
        elif self.accept(TokenType.String):
            assert self.last is not None
            node = self.node_exit(StringValueNode(self.last.lexeme))
        elif self.accept(TokenType.Integer):
            assert self.last is not None
            try:
                value, base = self.last.lexeme
                node = self.node_exit(IntValueNode(int(value, base), base))
            except TypeError:
                node = self.node_exit(IntValueNode(self.last.lexeme, 10))
        elif self.accept(TokenType.Float):
            assert self.last is not None
            lhs, rhs = self.last.lexeme
            node = self.node_exit(FloatValueNode(int(lhs), int(rhs)))
        elif self.accept(TokenType.Name, "true") or self.accept(
            TokenType.Name, "false"
        ):
            assert self.last is not None
            node = self.node_exit(BoolValueNode(bool(self.last.lexeme)))
        elif self.accept(TokenType.Template):
            assert self.last is not None
            name, definition = self.last.lexeme
            node = self.node_exit(TemplateValueNode(name, definition))
        else:
            self.node_cancel()
            node = self.lvalue()

        # Parse a function call (if it exists)
        if self.match(TokenType.ParenOpen):
            node = self.function(node)

        # Parse a cast (if it exists)
        if self.accept(TokenType.Reserved, ReservedWord.As):
            paren = False
            if self.accept(TokenType.ParenOpen):
                paren = True

            tp = self.declaration_type()
            node = CastNode(node, tp)

            if paren:
                self.expect(TokenType.ParenClose)

        return node

    def function(self, func: ExpressionNode) -> FunctionNode:
        """
        Parse a function call.
        """

        self.node_enter()

        self.expect(TokenType.ParenOpen)
        if self.accept(TokenType.ParenClose):
            return self.node_exit(FunctionNode(func, []))

        args = [self.expression()]
        while self.accept(TokenType.Comma):
            arg = self.expression()
            args.append(arg)
        self.expect(TokenType.ParenClose)

        return self.node_exit(FunctionNode(func, args))

    def array(self, target: ExpressionNode) -> ArrayNode:
        if not self.match(TokenType.BracketOpen):
            assert self.current is not None
            raise ParseError(self.current, "expected opening bracket")

        node: Any = target
        while self.accept(TokenType.BracketOpen):
            index = self.expression()
            self.expect(TokenType.BracketClose)
            result = ArrayNode(node, index)
            result.token_start = node.token_start
            result.token_end = self.last
            node = result

        return node

    def lvalue(self) -> LvalueNode:
        """
        Parse a left-hand side value.
        """

        if self.accept(TokenType.ParenOpen):
            expr = self.expression()
            self.expect(TokenType.ParenClose)
            try:
                expr = self.array(expr)
            except ParseError:
                pass

            if isinstance(expr, (LiteralNode, DerefNode, ArrayNode, VariableNode)):
                return expr
            else:
                assert self.current is not None
                raise ParseError(self.current, "expression is not a valid lvalue")

        self.node_enter()

        node: LvalueNode
        if self.accept(TokenType.Literal):
            assert self.last is not None
            node = self.node_exit(LiteralNode(self.last.lexeme))
        elif self.accept(TokenType.Times):
            target = self.atom()
            node = self.node_exit(DerefNode(target))
        else:
            name = self.expect(TokenType.Name)
            if name.lexeme in ("null", "NULL"):
                node = self.node_exit(LiteralNode("NULL"))
            else:
                node = self.node_exit(VariableNode(name.lexeme))

        try:
            node = self.array(node)
        except ParseError:
            pass

        return node

    def declaration(self) -> DeclarationNode:
        """
        Parse a variable declaration.
        """

        self.node_enter()

        var = self.expect(TokenType.Name)
        self.expect(TokenType.Colon, fail_msg="expected type specifier after name")
        var_type = self.declaration_type()

        initial: Optional[ExpressionNode] = None
        if self.accept(TokenType.Assign):
            initial = self.expression()

        return self.node_exit(DeclarationNode(var.lexeme, var_type, initial))

    def declaration_type(self) -> TypeNode:
        """
        Parse the type portion of a variable declaration.
        """

        self.node_enter()

        if self.accept(TokenType.Times):
            base = self.declaration_type()
            return self.node_exit(PointerTypeNode(base))
        elif self.accept(TokenType.BracketOpen):
            size = self.expect(TokenType.Integer)
            self.expect(TokenType.BracketClose)
            base = self.declaration_type()
            return self.node_exit(ArrayTypeNode(base, int(*size.lexeme)))
        elif self.accept(TokenType.Reserved, ReservedWord.Function):
            args = []
            variadic = False
            self.expect(TokenType.ParenOpen)
            if not self.accept(TokenType.ParenClose):
                while True:
                    if self.accept(TokenType.Ellipsis):
                        variadic = True
                        break

                    args.append(self.declaration_type())
                    if not self.accept(TokenType.Comma):
                        break

                self.expect(TokenType.ParenClose)

            ret = self.declaration_type()
            return self.node_exit(FuncTypeNode(ret, args, variadic))
        else:
            core = self.expect(TokenType.Name)
            return self.node_exit(SimpleTypeNode(core.lexeme))

    def end_of_line(self, after: Optional[str] = None):
        """
        Assert (and consume) the end of a line.

        This is a separate function, because:
        1. EOL can be signified by a Newline token or an EOF token
        2. Error handling is very generic
        """

        if self.accept(TokenType.Newline):
            return
        elif self.accept(TokenType.EOF):
            return
        else:
            msg = "expected a newline"
            if after:
                msg += " after " + after

            if self.last is not None:
                raise ParseError(self.last, msg)
            else:
                assert self.current is not None
                raise ParseError(self.current, msg)

    def expect(
        self,
        ttype: TokenType,
        lexeme: Optional[Any] = None,
        fail_msg: Optional[str] = None,
    ) -> Token:
        """
        Attempt to consume a token of the provided type (and optional lexeme).

        This function *always* succeeds, or raises an exception. This
        exception should not be caught, for a non-raising equivalent of this
        function see accept().
        """

        assert self.current is not None

        result = self.accept(ttype, lexeme)
        if result is None:
            if fail_msg:
                raise ParseError(self.current, fail_msg)
            else:
                ttype_name = PRINTABLE_NAMES[ttype]
                current_name = PRINTABLE_NAMES[self.current.ttype]
                raise ParseError(
                    self.current, f"expected {ttype_name} but got {current_name}"
                )

        return result

    def match(self, ttype: TokenType, lexeme: Optional[Any] = None) -> Optional[Token]:
        """
        Attempt to match a token of the provided type (and optional lexeme).
        """

        assert self.current is not None

        if self.current.ttype == ttype:
            if lexeme is None or self.current.lexeme == lexeme:
                return self.last

        return None

    def accept(self, ttype: TokenType, lexeme: Optional[Any] = None) -> Optional[Token]:
        """
        Attempt to consume a token of the provided type (and optional lexeme).
        """

        assert self.current is not None

        if self.current.ttype == ttype:
            if lexeme is None or self.current.lexeme == lexeme:
                self.advance()
                return self.last

        return None

    def peek(self) -> Optional[Token]:
        """
        Lookahead to the next available token.

        This is used to prevent requiring backtracking, since the grammar is
        LL(1) we can just use lookahead.
        """

        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1]
        else:
            return None

    def advance(self):
        """
        Move to the next token.
        """

        self.pos += 1
        self.last = self.current
        if self.pos < len(self.tokens):
            self.current = self.tokens[self.pos]
        else:
            self.current = None

    def node_enter(self):
        self.starts.append(self.pos)

    def node_cancel(self):
        self.starts.pop()

    def node_exit(self, node: N) -> N:
        node.token_start = self.tokens[self.starts.pop()]
        node.token_end = self.tokens[self.pos - 1]
        return node
