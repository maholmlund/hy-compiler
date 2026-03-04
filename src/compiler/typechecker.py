from dataclasses import dataclass
from typing import Self
from compiler.ast import *
from compiler.symtab import *


def typecheck(node: Expression) -> Type:
    symtab = SymTab[Type](None, global_symbols)
    return typecheck_rec(node, symtab)


def typecheck_rec(node: Expression, symtab: SymTab) -> Type:
    match node:
        case Literal():
            if type(node.value) == int:
                node.type = Int
                return Int
            elif type(node.value) == bool:
                node.type = Bool
                return Bool
            else:
                node.type = Unit
                return Unit
        case BinaryOp():
            left = typecheck_rec(node.left, symtab)
            right = typecheck_rec(node.right, symtab)
            if node.op == "==" or node.op == "!=":
                if left != right:
                    raise Exception(
                        f"{node.loc}: different types, left is {left} and right is {right}")
                node.type = Bool
                return Bool
            if node.op == "=":
                if not isinstance(node.left, Identifier):
                    raise Exception(f"{node.left.loc}: expected variable name")
                var_type = symtab.find(node.left.name)
                if var_type is None:
                    raise Exception(f"{node.left.loc}: unknown variable")
                if var_type != right:
                    raise Exception(
                        f"{node.loc}: operands must have the same type")
                node.type = var_type
                return var_type
            op_func_type = global_symbols[node.op]
            assert isinstance(op_func_type, FunType)
            if left != op_func_type.args[0]:
                raise Exception(
                    f"{node.left.loc}: expected {op_func_type.args[0]}")
            if right != op_func_type.args[1]:
                raise Exception(
                    f"{node.right.loc}: expected {op_func_type.args[1]}")
            node.type = op_func_type.value
            return op_func_type.value
        case UnaryOp():
            target = typecheck_rec(node.target, symtab)
            if node.op == "-":
                if target != Int:
                    raise Exception(f"{node.loc}: - only allowed for int type")
                node.type = Int
                return Int
            elif node.op == "not":
                if target != Bool:
                    raise Exception(
                        f"{node.loc}: 'not' only allowed for bool type")
                node.type = Bool
                return Bool
        case Identifier():
            var_type = symtab.find(node.name)
            if var_type is None:
                raise Exception(f"{node.loc}: unknown symbol")
            node.type = var_type
            return var_type
        case IfBlock():
            condition = typecheck_rec(node.condition, symtab)
            if condition != Bool:
                raise Exception(f"{node.loc}: expected bool type")
            then = typecheck_rec(node.then, symtab)
            if node.eelse is None:
                node.type = then
                return then
            eelse = typecheck_rec(node.eelse, symtab)
            if then != eelse:
                raise Exception(
                    f"{node.loc}: mismatching types for if block: then is {then} and else is {eelse}")
            node.type = then
            return then
        case While():
            condition = typecheck_rec(node.condition, symtab)
            if condition != Bool:
                raise Exception(f"{node.loc}: expected bool condition")
            node.type = Unit
            return Unit
        case Block():
            new_symtab = SymTab(symtab, dict())
            return_unit = isinstance(
                node.expressions[-1], Literal) and node.expressions[-1].value is None
            last_value = typecheck_rec(node.expressions[0], new_symtab)
            for e in node.expressions[1:]:
                last_value = typecheck_rec(e, new_symtab)
            if return_unit:
                node.type = Unit
                return Unit
            node.type = last_value
            return last_value
        case FunctionCall():
            return_type = symtab.require(node.name)
            assert (isinstance(return_type, FunType))
            if len(node.args) != len(return_type.args):
                raise Exception(
                    f"{node.loc}: invalid number of function arguments")
            for (i, arg) in enumerate(node.args):
                arg_type = typecheck_rec(arg, symtab)
                if arg_type != return_type.args[i]:
                    raise Exception(
                        f"{arg.loc}: invalid type for function argument")
                node.args[i].type = arg_type
            node.type = return_type.value
            return return_type.value
        case VarDeclaration():
            if node.name in symtab.symbols:
                raise Exception(
                    f"{node.loc}: redeclaration of a variable in the same scope")
            var_type = typecheck_rec(node.value, symtab)
            if node.var_type and var_type != node.var_type:
                raise Exception(f"{node.loc}: mismatching type declaration")
            symtab.symbols[node.name] = var_type
            node.type = Unit
            return Unit
        case Break():
            return Unit
        case Continue():
            return Unit
    node.type = Unit
    return Unit
