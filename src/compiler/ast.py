from dataclasses import dataclass


@dataclass
class Expression:
    pass


@dataclass
class Literal(Expression):
    value: int | bool


@dataclass
class Identifier(Expression):
    name: str


@dataclass
class BinaryOp(Expression):
    left: Expression
    op: str
    right: Expression


@dataclass
class UnaryOp(Expression):
    op: str
    target: Expression


@dataclass
class IfBlock(Expression):
    condition: Expression
    then: Expression
    eelse: Expression | None


@dataclass
class FunctionCall(Expression):
    name: str
    args: list[Expression]


@dataclass
class Block(Expression):
    expressions: list[Expression]


@dataclass
class VarDeclaration(Expression):
    name: str
    value: Expression
