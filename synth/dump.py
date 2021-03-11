import enum


@enum.unique
class DumpType(enum.Enum):
    AST = 1
    ASTDiagram = 2

    GraphBlock = 3
    GraphBlockChunk = 4
