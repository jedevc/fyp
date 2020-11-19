from typing import List, Optional, Union

from . import token
from .error import ParseError
from .node import (
    AssignmentNode,
    BlockNode,
    CallNode,
    ChunkNode,
    DeclarationNode,
    Expression,
    FunctionNode,
    GlobalChunkNode,
    Node,
    SpecialDeclarationNode,
    SpecNode,
    Statement,
    TypeNode,
    ValueNode,
    VariableNode,
)
from .token import Token, TokenType


class NodeFactory:
    def __init__(self, parser: "Parser"):
        self.parser = parser
        self.starts: List[int] = []

    def node_enter(self):
        self.starts.append(self.parser.pos)

    def node_cancel(self):
        self.starts.pop()

    def node_exit(self, node, *args):
        start = self.parser.tokens[self.starts.pop()]
        end = self.parser.tokens[self.parser.pos - 1]
        return node(start, end, *args)


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

        self.factory = NodeFactory(self)

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

        self.factory.node_enter()

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

            if self.current.lexeme == "chunk":
                chunks.append(self.chunk())
            elif self.current.lexeme == "global":
                chunks.append(self.global_chunk())
            elif self.current.lexeme == "block":
                blocks.append(self.block())
            else:
                raise ParseError(self.current, "unknown statement type")

        return self.factory.node_exit(SpecNode, chunks, blocks)

    def chunk(self) -> ChunkNode:
        """
        Parse a chunk of variables.
        """

        self.factory.node_enter()

        self.expect(TokenType.Reserved, "chunk")
        variables = [self.declaration()]
        while self.accept(TokenType.Comma):
            self.accept(TokenType.Newline)
            variables.append(self.declaration())
        self.end_of_line(after="chunk")

        return self.factory.node_exit(ChunkNode, variables)

    def global_chunk(self) -> GlobalChunkNode:
        """
        Parse a chunk of global variables.
        """

        self.factory.node_enter()

        self.expect(TokenType.Reserved, "global")
        variables = [self.declaration()]
        while self.accept(TokenType.Comma):
            self.accept(TokenType.Newline)
            variables.append(self.declaration())
        self.end_of_line(after="global")

        return self.factory.node_exit(GlobalChunkNode, variables)

    def block(self) -> BlockNode:
        """
        Parse a block of statements.
        """

        self.factory.node_enter()

        self.expect(TokenType.Reserved, "block")

        block_name = self.expect(TokenType.Name).lexeme
        self.expect(TokenType.BraceOpen)
        self.accept(TokenType.Newline)

        statements = []
        while True:
            if self.accept(TokenType.BraceClose):
                break

            self.factory.node_enter()
            stmt: Statement
            if self.accept(TokenType.Reserved, "call"):
                target = self.expect(TokenType.Name)
                stmt = self.factory.node_exit(CallNode, target.lexeme)
            elif (
                peek := self.peek()
            ) and peek.ttype == TokenType.Equals:  # pylint: disable=used-before-assignment
                target = self.expect(TokenType.Name)
                self.expect(TokenType.Equals)
                exp = self.expression()
                stmt = self.factory.node_exit(AssignmentNode, target.lexeme, exp)
            else:
                self.factory.node_cancel()
                stmt = self.expression()

            statements.append(stmt)
            self.end_of_line(after="statement")

        return self.factory.node_exit(BlockNode, block_name, statements)

    def expression(self) -> Expression:
        """
        Parse an expression.
        """

        self.factory.node_enter()

        if self.accept(TokenType.String):
            assert self.last is not None
            return self.factory.node_exit(ValueNode, self.last.lexeme)
        if self.accept(TokenType.Integer):
            assert self.last is not None
            return self.factory.node_exit(ValueNode, int(self.last.lexeme))
        elif (
            peek := self.peek()
        ) and peek.ttype == TokenType.ParenOpen:  # pylint: disable=used-before-assignment
            self.factory.node_cancel()
            return self.function()
        else:
            self.factory.node_cancel()
            return self.variable()

    def function(self) -> FunctionNode:
        """
        Parse a function call.
        """

        self.factory.node_enter()

        name = self.expect(TokenType.Name)

        self.expect(TokenType.ParenOpen)
        if self.accept(TokenType.ParenClose):
            return self.factory.node_exit(FunctionNode, name.lexeme, [])

        args = [self.expression()]
        while self.accept(TokenType.Comma):
            arg = self.expression()
            args.append(arg)
        self.expect(TokenType.ParenClose)

        return self.factory.node_exit(FunctionNode, name.lexeme, args)

    def variable(self) -> VariableNode:
        """
        Parse a variable reference.
        """

        self.factory.node_enter()

        addressed = self.accept(TokenType.AddressOf) is not None
        name = self.expect(TokenType.Name)
        return self.factory.node_exit(VariableNode, name.lexeme, addressed)

    def declaration(self) -> Union[DeclarationNode, SpecialDeclarationNode]:
        """
        Parse a variable declaration.
        """

        self.factory.node_enter()

        var = self.expect(TokenType.Name)
        if var.lexeme[0] == "$":
            return self.factory.node_exit(SpecialDeclarationNode, var.lexeme[1:])

        self.expect(TokenType.Colon, fail_msg="expected type specifier after name")
        var_type = self.declaration_type()

        return self.factory.node_exit(DeclarationNode, var.lexeme, var_type)

    def declaration_type(self) -> TypeNode:
        """
        Parse the type portion of a variable declaration.
        """

        self.factory.node_enter()

        base = self.expect(TokenType.Name)
        if self.accept(TokenType.BracketOpen):
            size = self.expect(TokenType.Integer)
            self.expect(TokenType.BracketClose)

            return self.factory.node_exit(TypeNode, base.lexeme, int(size.lexeme))

        return self.factory.node_exit(TypeNode, base.lexeme)

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
        lexeme: Optional[str] = None,
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
                ttype_name = token.PRINTABLE_NAMES[ttype]
                current_name = token.PRINTABLE_NAMES[self.current.ttype]
                raise ParseError(
                    self.current, f"expected {ttype_name} but got {current_name}"
                )

        return result

    def accept(self, ttype: TokenType, lexeme: Optional[str] = None) -> Optional[Token]:
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
