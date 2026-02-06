from dataclasses import dataclass
from typing import Self
from compiler.ast import *


class Type:
    pass


@dataclass
class FunType(Type):
    args: list[Type]
    value: Type


Unit = Type()
Int = Type()
Bool = Type()


@dataclass
class SymTab:
    parent: Self | None
    symbols: dict[str, Type | None]

    def find(self, name: str) -> None | Type:
        result = None
        current: SymTab | None = self
        while current is not None:
            if name in current.symbols:
                result = current.symbols[name]
                break
            current = current.parent
        return result


global_symbols = {
    '+': FunType([Int, Int], Int),
    '-': FunType([Int, Int], Int),
    '*': FunType([Int, Int], Int),
    '/': FunType([Int, Int], Int),
    '%': FunType([Int, Int], Int),
    'and': FunType([Int, Int], Bool),
    'or': FunType([Int, Int], Bool),
    '<=': FunType([Int, Int], Bool),
    '>=': FunType([Int, Int], Bool),
    '>': FunType([Int, Int], Bool),
    '<': FunType([Int, Int], Bool),
}


def typecheck(node: Expression) -> Type:
    symtab = SymTab(None, dict())
    return typecheck_rec(node, symtab)


def typecheck_rec(node: Expression, symtab: SymTab) -> Type:
    match node:
        case Literal():
            if type(node.value) == int:
                return Int
            return Bool
        case BinaryOp():
            left = typecheck_rec(node.left, symtab)
            right = typecheck_rec(node.right, symtab)
            if node.op == "==" or node.op == "!=":
                if left != right:
                    raise Exception(
                        f"{node.loc}: different types, left is {left} and right is {right}")
                return Bool
            if node.op == "=":
                right = typecheck_rec(node.right, symtab)
                if not isinstance(node.left, Identifier):
                    raise Exception(f"{node.left.loc}: expected variable name")
                var_type = symtab.find(node.left.name)
                if var_type is None:
                    raise Exception(f"{node.left.loc}: unknown variable")
                return var_type
            if left != global_symbols[node.op].args[0]:
                raise Exception(
                    f"{node.left.loc}: expected {global_symbols[node.op].args[0]}")
            if right != global_symbols[node.op].args[1]:
                raise Exception(
                    f"{node.right.loc}: expected {global_symbols[node.op].args[1]}")
            return global_symbols[node.op].value
        case UnaryOp():
            target = typecheck_rec(node, symtab)
            if node.op == "-":
                if target != Int:
                    raise Exception(f"{node.loc}: - only allowed for int type")
                return Int
            elif node.op == "not":
                if target != Bool:
                    raise Exception(
                        f"{node.loc}: 'not' only allowed for bool type")
                return Bool
        case Identifier():
            var_type = symtab.find(node.name)
            if var_type is None:
                raise Exception(f"{node.loc}: unknown symbol")
            return var_type
        case IfBlock():
            condition = typecheck_rec(node.condition, symtab)
            if condition != Bool:
                raise Exception(f"{node.loc}: expected bool type")
            then = typecheck_rec(node.then, symtab)
            if node.eelse is None:
                return then
            eelse = typecheck_rec(node.eelse, symtab)
            if then != eelse:
                raise Exception(
                    f"{node.loc}: mismatching types for if block: then is {then} and else is {eelse}")
            return then
        case While():
            condition = typecheck_rec(node.condition, symtab)
            if condition != Bool:
                raise Exception(f"{node.loc}: expected bool condition")
            return Unit
        case Block():
            new_symtab = SymTab(symtab, dict())
            return_unit = node.expressions[-1] == None
            last_value = typecheck_rec(node.expressions[0], new_symtab)
            for e in node.expressions[1:]:
                last_value = typecheck_rec(e, new_symtab)
            if return_unit:
                return Unit
            return last_value
        case FunctionCall():
            return_type = symtab.find(node.name)
            if return_type is None:
                raise Exception(f"{node.loc}: unknown function")
            assert (isinstance(return_type, FunType))
            return return_type.value
        case VarDeclaration():
            if node.name in symtab.symbols:
                raise Exception(
                    f"{node.loc}: redeclaration of a variable in the same scope")
            symtab.symbols[node.name] = typecheck_rec(node.value, symtab)
            return Unit
    return Unit
