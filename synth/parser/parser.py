from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from ..node import (
    ArrayNode,
    ArrayTypeNode,
    AssignmentNode,
    BinaryOperationNode,
    BlockNode,
    CallNode,
    ChunkNode,
    DeclarationNode,
    DerefNode,
    ExpressionNode,
    ExpressionStatementNode,
    ExternChunkNode,
    FunctionNode,
    FuncTypeNode,
    IfNode,
    IntValueNode,
    LvalueNode,
    Node,
    Operator,
    PointerTypeNode,
    RefNode,
    SimpleTypeNode,
    SpecialDeclarationNode,
    SpecNode,
    SplitNode,
    StatementNode,
    StringValueNode,
    TypeNode,
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
        variables = [self.declaration()]
        while self.accept(TokenType.Comma):
            self.accept(TokenType.Newline)
            variables.append(self.declaration())
        self.end_of_line(after="chunk")

        return self.node_exit(ChunkNode(variables))

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

        block_name = self.expect(TokenType.Name).lexeme
        statements = self.scope()
        return self.node_exit(BlockNode(block_name, statements))

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
            # FIXME: backtracking is sad :(
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
            self.atom,
            self.product,
            {
                TokenType.Times: Operator.Multiply,
                TokenType.Divide: Operator.Divide,
            },
        )

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

        if self.accept(TokenType.ParenOpen):
            self.node_cancel()

            node = self.expression()
            self.expect(TokenType.ParenClose)
            return node
        elif self.accept(TokenType.AddressOf):
            target = self.lvalue()
            return self.node_exit(RefNode(target))
        elif self.accept(TokenType.String):
            assert self.last is not None
            return self.node_exit(StringValueNode(self.last.lexeme))
        elif self.accept(TokenType.Integer):
            assert self.last is not None
            value, base = self.last.lexeme
            return self.node_exit(IntValueNode(int(value, base), base))
        elif (
            peek := self.peek()
        ) and peek.ttype == TokenType.ParenOpen:  # pylint: disable=used-before-assignment
            self.node_cancel()
            return self.function()
        else:
            self.node_cancel()
            return self.lvalue()

    def function(self) -> FunctionNode:
        """
        Parse a function call.
        """

        self.node_enter()

        name = self.expect(TokenType.Name)

        self.expect(TokenType.ParenOpen)
        if self.accept(TokenType.ParenClose):
            return self.node_exit(FunctionNode(name.lexeme, []))

        args = [self.expression()]
        while self.accept(TokenType.Comma):
            arg = self.expression()
            args.append(arg)
        self.expect(TokenType.ParenClose)

        return self.node_exit(FunctionNode(name.lexeme, args))

    def lvalue(self) -> LvalueNode:
        """
        Parse a left-hand side value.
        """

        self.node_enter()

        if self.accept(TokenType.ParenOpen):
            self.node_cancel()

            node = self.lvalue()
            self.expect(TokenType.ParenClose)
        elif self.accept(TokenType.Times):
            target = self.lvalue()
            node = self.node_exit(DerefNode(target))
        else:
            name = self.expect(TokenType.Name)
            node = self.node_exit(VariableNode(name.lexeme))

        while self.accept(TokenType.BracketOpen):
            # try to read optional array indexes at end
            index = self.expression()
            self.expect(TokenType.BracketClose)
            result = ArrayNode(node, index)
            result.token_start = node.token_start
            result.token_end = self.last
            node = result

        return node

    def declaration(self) -> Union[DeclarationNode, SpecialDeclarationNode]:
        """
        Parse a variable declaration.
        """

        self.node_enter()

        var = self.expect(TokenType.Name)
        if var.lexeme[0] == "$":
            return self.node_exit(SpecialDeclarationNode(var.lexeme[1:]))

        self.expect(TokenType.Colon, fail_msg="expected type specifier after name")
        var_type = self.declaration_type()

        return self.node_exit(DeclarationNode(var.lexeme, var_type))

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
            self.expect(TokenType.ParenOpen)
            if not self.accept(TokenType.ParenClose):
                args.append(self.declaration_type())
                while self.accept(TokenType.Comma):
                    args.append(self.declaration_type())
                self.expect(TokenType.ParenClose)

            ret = self.declaration_type()

            return self.node_exit(FuncTypeNode(ret, args))
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
