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

    def new_label(loc: Loc) -> Label:
        nonlocal label_counter
        label_counter += 1
        return Label(loc, f"L{label_counter}")

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

            case BinaryOp() if expr.op == "=":
                assert isinstance(expr.left, Identifier)
                target = symtab.require(expr.left.name)
                value = visit(symtab, expr.right)
                ins.append(Copy(loc, value, target))
                return value

            case BinaryOp() if expr.op == "or" or expr.op == "and":
                skip_label = new_label(loc)
                no_skip_label = new_label(loc)
                result = new_var()
                left = visit(symtab, expr.left)
                ins.append(Copy(loc, left, result))
                if expr.op == "and":
                    ins.append(CondJump(loc, left, no_skip_label, skip_label))
                else:
                    ins.append(CondJump(loc, left, skip_label, no_skip_label))
                ins.append(no_skip_label)
                right = visit(symtab, expr.right)
                ins.append(Copy(loc, right, result))
                ins.append(skip_label)
                return result

            case BinaryOp():
                var_op = symtab.require(expr.op)
                var_left = visit(symtab, expr.left)
                var_right = visit(symtab, expr.right)
                var_result = new_var()
                ins.append(Call(
                    loc, var_op, [var_left, var_right], var_result))
                return var_result

            case UnaryOp():
                target = visit(symtab, expr.target)
                result = new_var()
                if expr.op == "not":
                    ins.append(Call(loc, symtab.require(
                        'unary_not'), [target], result))
                else:
                    ins.append(Call(loc, symtab.require(
                        'unary_-'), [target], result))
                return result

            case IfBlock():
                if expr.eelse:
                    then_label = new_label(loc)
                    else_label = new_label(loc)
                    end_label = new_label(loc)
                    result = new_var()
                    cond = visit(symtab, expr.condition)
                    ins.append(CondJump(loc, cond, then_label, else_label))
                    ins.append(then_label)
                    result = visit(symtab, expr.then)
                    ins.append(Jump(loc, end_label))
                    ins.append(else_label)
                    result = visit(symtab, expr.eelse)
                    ins.append(end_label)
                    return result
                skip_label = new_label(loc)
                no_skip_label = new_label(loc)
                cond = visit(symtab, expr.condition)
                ins.append(CondJump(loc, cond, no_skip_label, skip_label))
                ins.append(no_skip_label)
                visit(symtab, expr.then)
                ins.append(skip_label)
                return var_unit

            case While():
                cond_label = new_label(loc)
                action_label = new_label(loc)
                end_label = new_label(loc)
                cond = new_var()
                ins.append(cond_label)
                cond = visit(symtab, expr.condition)
                ins.append(CondJump(loc, cond, action_label, end_label))
                ins.append(action_label)
                visit(symtab, expr.action)
                ins.append(Jump(loc, cond_label))
                ins.append(end_label)
                return var_unit

            case FunctionCall():
                function = symtab.require(expr.name)
                args = []
                for a in expr.args:
                    var = new_var()
                    var = visit(symtab, a)
                    args.append(var)
                result = new_var()
                ins.append(Call(loc, function, args, result))
                return result

            case Block():
                result = visit(symtab, expr.expressions[0])
                for e in expr.expressions[1:]:
                    result = visit(symtab, e)
                if isinstance(expr.expressions[-1], Literal) and expr.expressions[-1].value is None:
                    return var_unit
                return result

            case VarDeclaration():
                return visit(symtab, expr.value)

        assert 1 == 2  # we should never get here
        return new_var()

    root_symtab = SymTab[IRVar](None, dict())
    for name in reserved_names:
        root_symtab.symbols[name] = IRVar(name)

    var_final_result = visit(root_symtab, root_expr)

    if root_expr.type == Int:
        ins.append(Call(root_expr.loc, IRVar(
            "print_int"), [var_final_result], new_var()))
    elif root_expr.type == Bool:
        ins.append(Call(root_expr.loc, IRVar(
            "print_bool"), [var_final_result], new_var()))
    return ins
