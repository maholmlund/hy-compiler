from dataclasses import dataclass
from typing import Self
from compiler.ast import *


@dataclass
class SymbolTable:
    symbols: dict[str, int | bool | None]
    parent: Self | None


def interpret_rec(ast: Expression, symboltable: SymbolTable) -> int | bool | None:
    match ast:
        case Block():
            last = None
            block_context = SymbolTable(dict(), symboltable)
            for e in ast.expressions:
                last = interpret_rec(e, block_context)
            return last
        case Literal():
            return ast.value

        case Identifier():
            value = None
            current: SymbolTable | None = symboltable
            while True:
                if current is None:
                    raise Exception(f"{ast.loc}: unknown identifier")
                if ast.name in current.symbols:
                    return current.symbols[ast.name]
                current = current.parent

        case BinaryOp():
            left = interpret_rec(ast.left, symboltable)
            right = interpret_rec(ast.right, symboltable)

            def validate_ints(left: int | bool | None, right: int | bool | None, op: str) -> tuple[int, int]:
                if not isinstance(left, int):
                    raise Exception(
                        f"{ast.left}: expected int for {op} operator")
                if not isinstance(right, int):
                    raise Exception(
                        f"{ast.right}: expected int for {op} operator")
                return (left, right)

            def validate_bools(left: int | bool | None, right: int | bool | None, op: str) -> tuple[bool, bool]:
                if not isinstance(left, bool):
                    raise Exception(
                        f"{ast.left}: expected bool for {op} operator")
                if not isinstance(right, bool):
                    raise Exception(
                        f"{ast.right}: expected bool for {op} operator")
                return (left, right)

            match ast.op:
                case "+":
                    (l, r) = validate_ints(interpret_rec(ast.left, symboltable),
                                           interpret_rec(ast.right, symboltable), ast.op)
                    return l + r
                case "-":
                    (l, r) = validate_ints(interpret_rec(ast.left, symboltable),
                                           interpret_rec(ast.right, symboltable), ast.op)
                    return l - r
                case "%":
                    (l, r) = validate_ints(interpret_rec(ast.left, symboltable),
                                           interpret_rec(ast.right, symboltable), ast.op)
                    return l % r
                case "*":
                    (l, r) = validate_ints(interpret_rec(ast.left, symboltable),
                                           interpret_rec(ast.right, symboltable), ast.op)
                    return l * r
                case "/":
                    (l, r) = validate_ints(interpret_rec(ast.left, symboltable),
                                           interpret_rec(ast.right, symboltable), ast.op)
                    return l // r  # TODO: maybe this is correct? language spec does not specify
                case "<":
                    (l, r) = validate_ints(interpret_rec(ast.left, symboltable),
                                           interpret_rec(ast.right, symboltable), ast.op)
                    return l < r
                case ">":
                    (l, r) = validate_ints(interpret_rec(ast.left, symboltable),
                                           interpret_rec(ast.right, symboltable), ast.op)
                    return l > r
                case "<=":
                    (l, r) = validate_ints(interpret_rec(ast.left, symboltable),
                                           interpret_rec(ast.right, symboltable), ast.op)
                    return l <= r
                case ">=":
                    (l, r) = validate_ints(interpret_rec(ast.left, symboltable),
                                           interpret_rec(ast.right, symboltable), ast.op)
                    return l >= r
                case "==":
                    (l, r) = validate_ints(interpret_rec(ast.left, symboltable),
                                           interpret_rec(ast.right, symboltable), ast.op)
                    return l == r
                case "!=":
                    (l, r) = validate_ints(interpret_rec(ast.left, symboltable),
                                           interpret_rec(ast.right, symboltable), ast.op)
                    return l != r
                case "or":
                    (l, r) = validate_bools(interpret_rec(ast.left, symboltable),
                                            interpret_rec(ast.right, symboltable), ast.op)
                    return l or r
                case "and":
                    (l, r) = validate_bools(interpret_rec(ast.left, symboltable),
                                            interpret_rec(ast.right, symboltable), ast.op)
                    return l and r
                case "=":
                    if not isinstance(ast.left, Identifier):
                        raise Exception(
                            f"{ast.left.loc}: not an identifier, expected for =")
                    value = interpret_rec(ast.right, symboltable)
                    current_context: SymbolTable | None = symboltable
                    while current_context:
                        if ast.left.name in current_context.symbols:
                            if type(current_context.symbols[ast.left.name]) != type(value):
                                raise Exception(
                                    f"{ast.left.loc}: tried changing variable type")
                            current_context.symbols[ast.left.name] = value
                            return None
                        current_context = current_context.parent
                    raise Exception(f"{ast.left.loc}: unknown identifier")

                case _:
                    raise Exception(f"{ast.loc}: unknown operator")
        case UnaryOp():
            target = interpret_rec(ast.target, symboltable)
            match ast.op:
                case "-":
                    if not isinstance(target, int):
                        raise Exception(f"{ast.loc}: expected int")
                    return -target
                case "not":
                    if not isinstance(target, bool):
                        raise Exception(f"{ast.loc}: expected bool")
                    return not target

        case VarDeclaration():
            symboltable.symbols[ast.name] = interpret_rec(
                ast.value, symboltable)
            return None

        case IfBlock():
            condition = interpret_rec(ast.condition, symboltable)
            if not isinstance(condition, bool):
                raise Exception(f"{ast.loc}: expected bool")
            if condition:
                return interpret_rec(ast.then, symboltable)
            if ast.eelse:
                return interpret_rec(ast.eelse, symboltable)
            return None

        case While():
            while True:
                condition = interpret_rec(ast.condition, symboltable)
                if not isinstance(condition, bool):
                    raise Exception(f"{ast.condition.loc}: expected bool")
                if not condition:
                    break
                interpret_rec(ast.action, symboltable)
            return None

        case FunctionCall():
            args = [interpret_rec(e, symboltable) for e in ast.args]
            if ast.name == "print_int":
                if len(args) != 1:
                    raise Exception(
                        f"{ast.loc}: invalid number of arguments for print_int")
                if not isinstance(args[0], int):
                    raise Exception(
                        f"{ast.loc}: argument for print_int is not an int")
                print(args[0])
                return None
            elif ast.name == "print_bool":
                if len(args) != 1:
                    raise Exception(
                        f"{ast.loc}: invalid number of arguments for print_bool")
                if not isinstance(args[0], int):
                    raise Exception(
                        f"{ast.loc}: argument for print_bool is not a bool")
                print(args[0])
                return None
            elif ast.name == "read_int":
                if len(args) != 0:
                    raise Exception(
                        f"{ast.loc}: invalid number of arguments for read_int")
                value = int(input("read_int: "))
                return value

        case Expression():
            return None

    raise Exception(f"{ast.loc}: unknown ast node: {type(ast)}")


def interpret(ast: Expression) -> int | bool | None:
    table = SymbolTable(dict(), None)
    result = interpret_rec(ast, table)
    return result
