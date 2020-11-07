from typing import List, Optional, Union

from .error import ParseError
from .token import Token, TokenType
from .node import (
    Node,
    SpecNode,
    BlockNode,
    CallNode,
    AssignmentNode,
    FunctionNode,
    VariableNode,
    ChunkNode,
    TypeNode,
    DeclarationNode,
    SpecialDeclarationNode,
    Expression,
)


class Parser:
    def __init__(self, tokens: List[Token]):
        assert len(tokens) >= 0

        self.pos = -1
        self.tokens = tokens

        self.current: Optional[Token] = None
        self.last: Optional[Token] = None

        self.stack: List[int] = []

    def save(self):
        self.stack.append(self.pos)

    def cancel(self):
        self.stack.pop()

    def backtrack(self):
        self.pos = self.stack.pop()
        self.current = self.tokens[self.pos]
        self.last = self.tokens[self.pos - 1]

    def parse(self) -> Node:
        self.advance()

        return self.spec()

    def spec(self) -> SpecNode:
        chunks = []
        blocks = []
        while self.pos < len(self.tokens):
            if self.accept(TokenType.EOF):
                break
            elif self.accept(TokenType.Newline):
                continue
            elif self.accept(TokenType.Reserved, "chunk"):
                chunks.append(self.chunk())
            elif self.accept(TokenType.Reserved, "block"):
                blocks.append(self.block())
            else:
                assert self.current is not None
                raise ParseError(self.current, "unknown statement type")

        return SpecNode(chunks, blocks)

    def chunk(self) -> ChunkNode:
        variables = [self.declaration()]
        while self.accept(TokenType.Comma):
            variables.append(self.declaration())
        self.end_of_line()
        return ChunkNode(variables)

    def block(self) -> BlockNode:
        block_name = self.expect(TokenType.Name).lexeme
        self.expect(TokenType.BraceOpen)

        statements = []
        while True:
            if self.accept(TokenType.BraceClose):
                break

            statement = self.any_of(self.call, self.assignment, self.expression)
            statements.append(statement)
            self.end_of_line()

        return BlockNode(block_name, statements)

    def call(self) -> CallNode:
        self.expect(TokenType.Reserved, "call")
        target = self.expect(TokenType.Name)
        return CallNode(target.lexeme)

    def assignment(self) -> AssignmentNode:
        target = self.expect(TokenType.Name)
        self.expect(TokenType.Equals)
        exp = self.expression()
        return AssignmentNode(target.lexeme, exp)

    def expression(self) -> Expression:
        return self.any_of(self.function, self.variable)

    def function(self) -> FunctionNode:
        name = self.expect(TokenType.Name)

        self.expect(TokenType.ParenOpen)
        if self.accept(TokenType.ParenClose):
            return FunctionNode(name.lexeme, [])

        args = [self.expression()]
        while self.accept(TokenType.Comma):
            arg = self.expression()
            args.append(arg)
        self.expect(TokenType.ParenClose)

        return FunctionNode(name.lexeme, args)

    def variable(self) -> VariableNode:
        addressed = self.accept(TokenType.AddressOf) is not None
        name = self.expect(TokenType.Name)
        return VariableNode(name.lexeme, addressed)

    def declaration(self) -> Union[DeclarationNode, SpecialDeclarationNode]:
        var = self.expect(TokenType.Name)
        if var.lexeme[0] == "$":
            return SpecialDeclarationNode(var.lexeme[1:])

        self.expect(TokenType.Colon, fail_msg="expected type specifier after name")
        var_type = self.declaration_type()

        return DeclarationNode(var.lexeme, var_type)

    def declaration_type(self) -> TypeNode:
        base = self.expect(TokenType.Name)
        if self.accept(TokenType.BracketOpen):
            size = self.expect(TokenType.Integer)
            self.expect(TokenType.BracketClose)

            return TypeNode(base.lexeme, int(size.lexeme))

        return TypeNode(base.lexeme)

    def end_of_line(self):
        if self.accept(TokenType.Newline):
            return
        elif self.accept(TokenType.EOF):
            return
        else:
            raise ParseError(self.last, "expected a newline")

    def any_of(self, *args):
        # FIXME: this function is *very* annoying to try and type

        result = None
        for attempt in args:
            try:
                self.save()
                result = attempt()
                break
            except ParseError:
                self.backtrack()
            else:
                self.cancel()

        if result is None:
            raise RuntimeError("yikes no expression")
        return result

    def expect(
        self,
        ttype: TokenType,
        lexeme: Optional[str] = None,
        fail_msg: Optional[str] = None,
    ) -> Token:
        assert self.current is not None

        result = self.accept(ttype, lexeme)
        if result is None:
            if fail_msg:
                raise ParseError(self.current, fail_msg)
            else:
                raise ParseError(
                    self.current, f"expected {ttype} but got {self.current.ttype}"
                )

        return result

    def accept(self, ttype: TokenType, lexeme: Optional[str] = None) -> Optional[Token]:
        assert self.current is not None

        if self.current.ttype == ttype:
            if lexeme is None or self.current.lexeme == lexeme:
                self.advance()
                return self.last

        return None

    def peek(self) -> Optional[Token]:
        return self.peekn(1)

    def peekn(self, n) -> Optional[Token]:
        if self.pos + n < len(self.tokens):
            return self.tokens[self.pos + n]
        return None

    def advance(self):
        self.pos += 1
        self.last = self.current
        if self.pos < len(self.tokens):
            self.current = self.tokens[self.pos]
        else:
            self.current = None
