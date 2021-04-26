import enum


@enum.unique
class DumpType(enum.Enum):
    Tokens = 1
    AST = 2
    ASTDiagram = 3

    GraphBlock = 4
    GraphBlockChunk = 5
