from dataclasses import dataclass
from typing import Self
from compiler.ast import *
from compiler.symtab import *


@dataclass
class Context:
    inside_function: bool
    symtab: SymTab
    function_ret_type: Type


def typecheck(node: Expression) -> Type:
    symtab = SymTab[Type](None, global_symbols)
    return typecheck_rec(node, Context(False, symtab, Unit))


def typecheck_rec(node: Expression, ctx: Context) -> Type:
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
            left = typecheck_rec(node.left, ctx)
            right = typecheck_rec(node.right, ctx)
            if node.op == "==" or node.op == "!=":
                if left != right:
                    raise Exception(
                        f"{node.loc}: different types, left is {left} and right is {right}")
                node.type = Bool
                return Bool
            if node.op == "=":
                if not isinstance(node.left, Identifier):
                    raise Exception(f"{node.left.loc}: expected variable name")
                var_type = ctx.symtab.find(node.left.name)
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
            target = typecheck_rec(node.target, ctx)
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
            var_type = ctx.symtab.find(node.name)
            if var_type is None:
                raise Exception(f"{node.loc}: unknown symbol")
            node.type = var_type
            return var_type
        case IfBlock():
            condition = typecheck_rec(node.condition, ctx)
            if condition != Bool:
                raise Exception(f"{node.loc}: expected bool type")
            then = typecheck_rec(node.then, ctx)
            if node.eelse is None:
                node.type = then
                return then
            eelse = typecheck_rec(node.eelse, ctx)
            if then != eelse:
                raise Exception(
                    f"{node.loc}: mismatching types for if block: then is {then} and else is {eelse}")
            node.type = then
            return then
        case While():
            condition = typecheck_rec(node.condition, ctx)
            if condition != Bool:
                raise Exception(f"{node.loc}: expected bool condition")
            node.type = Unit
            typecheck_rec(node.action, ctx)
            return Unit
        case Block():
            new_ctx = Context(ctx.inside_function, SymTab(
                ctx.symtab, dict()), ctx.function_ret_type)
            return_unit = isinstance(
                node.expressions[-1], Literal) and node.expressions[-1].value is None
            last_value = typecheck_rec(node.expressions[0], new_ctx)
            for e in node.expressions[1:]:
                last_value = typecheck_rec(e, new_ctx)
            if return_unit:
                node.type = Unit
                return Unit
            node.type = last_value
            return last_value
        case FunctionCall():
            return_type = ctx.symtab.require(node.name)
            assert (isinstance(return_type, FunType))
            if len(node.args) != len(return_type.args):
                raise Exception(
                    f"{node.loc}: invalid number of function arguments")
            for (i, arg) in enumerate(node.args):
                arg_type = typecheck_rec(arg, ctx)
                if arg_type != return_type.args[i]:
                    raise Exception(
                        f"{arg.loc}: invalid type for function argument")
                node.args[i].type = arg_type
            node.type = return_type.value
            return return_type.value
        case VarDeclaration():
            if node.name in ctx.symtab.symbols:
                raise Exception(
                    f"{node.loc}: redeclaration of a variable in the same scope")
            var_type = typecheck_rec(node.value, ctx)
            if node.var_type and var_type != node.var_type:
                raise Exception(f"{node.loc}: mismatching type declaration")
            ctx.symtab.symbols[node.name] = var_type
            node.type = Unit
            return Unit
        case Break():
            node.type = Unit
            return Unit
        case Continue():
            node.type = Unit
            return Unit
        case Module():
            new_ctx = Context(False, SymTab(ctx.symtab, dict()), Unit)
            for f in node.functions:
                if new_ctx.symtab.find(f.name):
                    raise Exception(
                        f"{f.loc}: redefinition of function {f.name}")
                new_ctx.symtab.symbols[f.name] = FunType(
                    [arg[1] for arg in f.args],
                    f.ret_val
                )
            for f in node.functions:
                ret_val = typecheck_rec(f, new_ctx)
            if len(node.expressions) == 0:
                return Unit
            for e in node.expressions[:-1]:
                typecheck_rec(e, new_ctx)
            last_value = typecheck_rec(node.expressions[-1], new_ctx)
            node.type = last_value
            return last_value
        case Function():
            new_symtab = SymTab(ctx.symtab, dict())
            for fun_arg in node.args:
                new_symtab.symbols[fun_arg[0]] = fun_arg[1]
            new_ctx = Context(True, new_symtab, node.ret_val)
            typecheck_rec(node.block, new_ctx)
            node.type = Unit
            return Unit
        case Return():
            if not ctx.inside_function:
                raise Exception(
                    f"{node.loc}: return only allowed inside functions")
            ret_val = typecheck_rec(node.value, ctx)
            if ret_val != ctx.function_ret_type:
                raise Exception(f"{node.loc}: wrong return type for function")
            node.type = Unit
            return Unit
    node.type = Unit
    return Unit
