from typing import List, Optional

from .token import Token, TokenType
from .node import *


class Parser:
    def __init__(self, tokens: List[Token]):
        self.pos = -1
        self.tokens = tokens

        self.current = None
        self.last = None
        self.advance()

    def spec(self) -> SpecNode:
        chunks = []
        while self.pos < len(self.tokens):
            if self.accept(TokenType.EOF):
                break
            if self.accept(TokenType.Newline):
                continue

            if self.accept(TokenType.Name, "chunk"):
                chunks.append(self.chunk())

        return SpecNode(chunks)

    def chunk(self) -> ChunkNode:
        variables = [self.variable()]
        if self.accept(TokenType.Comma):
            variables.append(self.variable())
        self.end_of_line()
        return ChunkNode(variables)

    def variable(self) -> VariableNode:
        var = self.expect(TokenType.Name)
        self.expect(TokenType.Colon, fail_msg="expected type specifier after name")
        var_type = self.expect(TokenType.Name)

        return VariableNode(var.lexeme, var_type.lexeme)

    def end_of_line(self):
        if self.accept(TokenType.Newline):
            return
        elif self.accept(TokenType.EOF):
            return
        else:
            raise RuntimeError("expected a newline")

    def expect(
        self,
        ttype: TokenType,
        lexeme: Optional[str] = None,
        fail_msg: Optional[str] = None,
    ) -> Token:
        result = self.accept(ttype, lexeme)
        if result is None:
            if fail_msg:
                raise RuntimeError(fail_msg)
            else:
                if self.current:
                    raise RuntimeError(f"expected {ttype} but got {self.current.ttype}")
                else:
                    raise RuntimeError(
                        f"expected {ttype} but there were no more tokens"
                    )

        return result

    def accept(self, ttype: TokenType, lexeme: Optional[str] = None) -> Optional[Token]:
        if self.current and self.current.ttype == ttype:
            if lexeme is None or self.current.lexeme == lexeme:
                self.advance()
                return self.last

        return None

    def peek(self) -> Optional[Token]:
        return self.peekn(1)

    def peekn(self, n) -> Optional[Token]:
        if self.pos + n < len(self.tokens):
            return self.tokens[self.pos + n]
        else:
            return None

    def advance(self):
        self.pos += 1
        self.last = self.current
        if self.pos < len(self.tokens):
            self.current = self.tokens[self.pos]
        else:
            self.current = None
