from compiler.symtab import *
from compiler import ast
from compiler import ir


@dataclass
class IRFunction:
    name: str
    args: list[ir.IRVar]
    ir: list[ir.Instruction]


def generate_ir(
    root_expr: Module
) -> list[IRFunction]:
    var_unit = ir.IRVar('unit')
    reserved_names = set(k for k in global_symbols.keys())
    var_counter = 0
    label_counter = 0
    result = []

    def new_var() -> ir.IRVar:
        nonlocal var_counter
        var_counter += 1
        return ir.IRVar(f"V{var_counter}")

    def new_label(loc: Loc) -> ir.Label:
        nonlocal label_counter
        label_counter += 1
        return ir.Label(loc, f"L{label_counter}")

    def generate_function_ir(
        root_expr: Expression,
        symtab: SymTab
    ) -> list[ir.Instruction]:
        loop_start_label: ir.Label | None = None
        loop_end_label: ir.Label | None = None

        ins: list[ir.Instruction] = []

        def visit(symtab: SymTab[ir.IRVar], expr: Expression) -> ir.IRVar:
            loc = expr.loc
            nonlocal loop_start_label
            nonlocal loop_end_label

            match expr:
                case ast.Literal():
                    match expr.value:
                        case bool():
                            var = new_var()
                            ins.append(ir.LoadBoolConst(
                                loc, expr.value, var))
                        case int():
                            var = new_var()
                            ins.append(ir.LoadIntConst(
                                loc, expr.value, var))
                        case None:
                            var = var_unit
                        case _:
                            raise Exception(
                                f"{loc}: unsupported literal: {type(expr.value)}")
                    return var

                case ast.Identifier():
                    return symtab.require(expr.name)

                case ast.BinaryOp() if expr.op == "=":
                    assert isinstance(expr.left, Identifier)
                    target = symtab.require(expr.left.name)
                    value = visit(symtab, expr.right)
                    ins.append(ir.Copy(loc, value, target))
                    return value

                case ast.BinaryOp() if expr.op == "or" or expr.op == "and":
                    skip_label = new_label(loc)
                    no_skip_label = new_label(loc)
                    result = new_var()
                    left = visit(symtab, expr.left)
                    ins.append(ir.Copy(loc, left, result))
                    if expr.op == "and":
                        ins.append(
                            ir.CondJump(loc, left, no_skip_label, skip_label))
                    else:
                        ins.append(
                            ir.CondJump(loc, left, skip_label, no_skip_label))
                    ins.append(no_skip_label)
                    right = visit(symtab, expr.right)
                    ins.append(ir.Copy(loc, right, result))
                    ins.append(skip_label)
                    return result

                case ast.BinaryOp():
                    var_op = symtab.require(expr.op)
                    var_left = visit(symtab, expr.left)
                    var_right = visit(symtab, expr.right)
                    var_result = new_var()
                    ins.append(ir.Call(
                        loc, var_op, [var_left, var_right], var_result))
                    return var_result

                case ast.UnaryOp():
                    target = visit(symtab, expr.target)
                    result = new_var()
                    if expr.op == "not":
                        ins.append(ir.Call(loc, symtab.require(
                            'unary_not'), [target], result))
                    else:
                        ins.append(ir.Call(loc, symtab.require(
                            'unary_-'), [target], result))
                    return result

                case ast.IfBlock():
                    if expr.eelse:
                        then_label = new_label(loc)
                        else_label = new_label(loc)
                        end_label = new_label(loc)
                        result = new_var()
                        cond = visit(symtab, expr.condition)
                        ins.append(ir.CondJump(
                            loc, cond, then_label, else_label))
                        ins.append(then_label)
                        ins.append(
                            ir.Copy(loc, visit(symtab, expr.then), result))
                        ins.append(ir.Jump(loc, end_label))
                        ins.append(else_label)
                        ins.append(
                            ir.Copy(loc, visit(symtab, expr.eelse), result))
                        ins.append(end_label)
                        return result
                    skip_label = new_label(loc)
                    no_skip_label = new_label(loc)
                    cond = visit(symtab, expr.condition)
                    ins.append(ir.CondJump(
                        loc, cond, no_skip_label, skip_label))
                    ins.append(no_skip_label)
                    visit(symtab, expr.then)
                    ins.append(skip_label)
                    return var_unit

                case ast.While():
                    cond_label = new_label(loc)
                    action_label = new_label(loc)
                    end_label = new_label(loc)
                    cond = new_var()
                    ins.append(cond_label)
                    old_loop_start = loop_start_label
                    old_loop_end = loop_end_label
                    loop_start_label = cond_label
                    loop_end_label = end_label
                    cond = visit(symtab, expr.condition)
                    ins.append(ir.CondJump(loc, cond, action_label, end_label))
                    ins.append(action_label)
                    visit(symtab, expr.action)
                    ins.append(ir.Jump(loc, cond_label))
                    ins.append(end_label)
                    loop_start_label = old_loop_start
                    loop_end_label = old_loop_end
                    return var_unit

                case ast.FunctionCall():
                    function = symtab.require(expr.name)
                    args = []
                    for a in expr.args:
                        var = new_var()
                        var = visit(symtab, a)
                        args.append(var)
                    result = new_var()
                    ins.append(ir.Call(loc, function, args, result))
                    return result

                case ast.Block():
                    new_tab = SymTab(symtab, {})
                    result = visit(new_tab, expr.expressions[0])
                    for e in expr.expressions[1:]:
                        result = visit(new_tab, e)
                    if isinstance(expr.expressions[-1], Literal) and expr.expressions[-1].value is None:
                        return var_unit
                    return result

                case ast.VarDeclaration():
                    value = visit(symtab, expr.value)
                    result = new_var()
                    ins.append(ir.Copy(loc, value, result))
                    symtab.symbols[expr.name] = result
                    return result

                case ast.Break():
                    if loop_end_label is None:
                        raise Exception(f"{loc}: break not inside loop")
                    ins.append(ir.Jump(loc, loop_end_label))
                    return var_unit

                case ast.Continue():
                    if loop_start_label is None:
                        raise Exception(f"{loc}: continue not inside loop")
                    ins.append(ir.Jump(loc, loop_start_label))
                    return var_unit

                case ast.Return():
                    ret_val = visit(symtab, expr.value)
                    ins.append(ir.Return(loc, ret_val))
                    return var_unit

            assert 1 == 2  # we should never get here
            return new_var()

        function_symtab = SymTab[ir.IRVar](symtab, dict())
        var_final_result = visit(function_symtab, root_expr)
        # if root_expr.type == Int:
        #     ins.append(Call(root_expr.loc, IRVar(
        #         "print_int"), [var_final_result], new_var()))
        # elif root_expr.type == Bool:
        #     ins.append(Call(root_expr.loc, IRVar(
        #         "print_bool"), [var_final_result], new_var()))
        return ins

    def create_main_function(expressions: list[Expression]) -> Function:
        if expressions[-1].type != Unit:
            func_name = ""
            if expressions[-1].type == Bool:
                func_name = "print_bool"
            elif expressions[-1].type == Int:
                func_name = "print_int"
            expressions[-1] = ast.FunctionCall(Loc(1, 1),
                                               func_name, [expressions[-1]], type=Unit)
        expressions.append(ast.Return(Loc(1, 1), Literal(
            Loc(1, 1), None, type=Unit), type=Unit))
        return Function(Loc(1, 1,), "main", [], Unit, Block(Loc(1, 1,), [e for e in expressions], type=Unit), type=Unit)

    module_symtab = SymTab[ir.IRVar](None, dict())
    for name in reserved_names:
        module_symtab.symbols[name] = ir.IRVar(name)
    for f in root_expr.functions:
        module_symtab.symbols[f.name] = ir.IRVar(f.name)

    root_expr.functions.append(create_main_function(root_expr.expressions))

    for f in root_expr.functions:
        func_args = [(a[0], new_var()) for a in f.args]
        function_declaration_symtab = SymTab(module_symtab, dict())
        for arg in func_args:
            function_declaration_symtab.symbols[arg[0]] = arg[1]
        # add function start
        result.append(IRFunction(
            f.name,
            [a[1] for a in func_args],
            generate_function_ir(f.block, function_declaration_symtab),
        ))
        # add function end
    return result
