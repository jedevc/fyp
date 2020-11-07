from typing import List, Optional, Union

from .error import ParseError
from .token import Token, TokenType
from .node import Node, SpecNode, ChunkNode, TypeNode, VariableNode, SpecialVariableNode


class Parser:
    def __init__(self, tokens: List[Token]):
        assert len(tokens) >= 0

        self.pos = -1
        self.tokens = tokens

        self.current: Optional[Token] = None
        self.last: Optional[Token] = None

    def parse(self) -> Node:
        self.advance()

        return self.spec()

    def spec(self) -> SpecNode:
        chunks = []
        while self.pos < len(self.tokens):
            if self.accept(TokenType.EOF):
                break
            elif self.accept(TokenType.Newline):
                continue
            elif self.accept(TokenType.Reserved, "chunk"):
                chunks.append(self.chunk())
            else:
                assert self.current is not None
                raise ParseError(self.current, "unknown statement type")

        return SpecNode(chunks)

    def chunk(self) -> ChunkNode:
        variables = [self.variable()]
        while self.accept(TokenType.Comma):
            variables.append(self.variable())
        self.end_of_line()
        return ChunkNode(variables)

    def variable(self) -> Union[VariableNode, SpecialVariableNode]:
        var = self.expect(TokenType.Name)
        if var.lexeme[0] == "$":
            return SpecialVariableNode(var.lexeme[1:])

        self.expect(TokenType.Colon, fail_msg="expected type specifier after name")
        var_type = self.variable_type()

        return VariableNode(var.lexeme, var_type)

    def variable_type(self) -> TypeNode:
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
