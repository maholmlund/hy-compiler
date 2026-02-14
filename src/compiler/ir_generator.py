from compiler.symtab import *
from compiler.ast import *
from compiler.ir import *


def generate_ir(
    root_expr: Expression
) -> list[Instruction]:
    var_unit = IRVar('unit')
    reserved_names = set(k for k in global_symbols.keys())
    var_counter = 0
    label_counter = 0

    def new_var() -> IRVar:
        nonlocal var_counter
        var_counter += 1
        return IRVar(f"V{var_counter}")

    def new_label() -> IRVar:
        nonlocal label_counter
        label_counter += 1
        return IRVar(f"L{label_counter}")

    ins: list[Instruction] = []

    def visit(symtab: SymTab[IRVar], expr: Expression) -> IRVar:
        loc = expr.loc

        match expr:
            case Literal():
                match expr.value:
                    case bool():
                        var = new_var()
                        ins.append(LoadBoolConst(
                            loc, expr.value, var))
                    case int():
                        var = new_var()
                        ins.append(LoadIntConst(
                            loc, expr.value, var))
                    case None:
                        var = var_unit
                    case _:
                        raise Exception(
                            f"{loc}: unsupported literal: {type(expr.value)}")
                return var

            case Identifier():
                return symtab.require(expr.name)

            case BinaryOp():
                var_op = symtab.require(expr.op)
                var_left = visit(symtab, expr.left)
                var_right = visit(symtab, expr.right)
                var_result = new_var()
                ins.append(Call(
                    loc, var_op, [var_left, var_right], var_result))
                return var_result

        assert 1 == 2
        return new_var()

    root_symtab = SymTab[IRVar](None, dict())
    for name in reserved_names:
        root_symtab.symbols[name] = IRVar(name)

    var_final_result = visit(root_symtab, root_expr)

    if root_expr.type == Int:
        ins.append(Call(root_expr.loc, IRVar(
            "print_int"), [var_final_result], var_unit))
    elif root_expr.type == Bool:
        ins.append(Call(root_expr.loc, IRVar(
            "print_bool"), [var_final_result], var_unit))
    return ins
