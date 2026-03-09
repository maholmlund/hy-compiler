from dataclasses import dataclass, field
from compiler.location import Loc


class Type:
    def __str__(self) -> str:
        if self == Unit:
            return "Unit"
        elif self == Int:
            return "Int"
        elif self == Bool:
            return "Bool"
        return "woops, something went wrong"


@dataclass
class FunType(Type):
    args: list[Type]
    value: Type


Unit = Type()
Int = Type()
Bool = Type()


@dataclass
class Expression:
    loc: Loc
    type: None | Type = field(default=None, kw_only=True)

    def __str__(self) -> str:
        match self:
            case Literal():
                return f"Literal(type: {self.type}, value: {self.value})"
            case Identifier():
                return f"Identifier(type: {self.type}, name: {self.name})"
            case BinaryOp():
                return f"BinaryOp(type: {self.type}, left: {self.left}, op: {self.op}, right: {self.right})"
            case UnaryOp():
                return f"UnaryOp(type: {self.type}, op: {self.op}, target: {self.target})"
            case IfBlock():
                return f"IfBlock(type: {self.type}, condition: {self.condition}, then: {self.then}, else: {self.eelse})"
            case While():
                return f"Wile(type: {self.type}, condition: {self.condition}, action: {self.action})"
            case FunctionCall():
                return f"FunctionCall(type: {self.type}, name: {self.name}, args: {self.args})"
            case Block():
                return f"Block(type: {self.type}, [{', '.join(str(e) for e in self.expressions)}])"
            case VarDeclaration():
                return f"VarDeclaration(type: {self.type}, name: {self.name}, value: {self.value})"
            case Break():
                return f"Break(type: {self.type})"
            case Continue():
                return f"Continue(type: {self.type})"
        return ""


@dataclass
class Literal(Expression):
    value: int | bool | None


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
class While(Expression):
    condition: Expression
    action: Expression


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
    var_type: Type | None = None


@dataclass
class Break(Expression):
    pass


@dataclass
class Continue(Expression):
    pass


@dataclass
class Function(Expression):
    name: str
    args: dict[str, Type]
    ret_val: Type
    block: Block


@dataclass
class Module(Expression):
    expressions: list[Expression]
    functions: list[Function]
