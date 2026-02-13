import pytest
from compiler.typechecker import typecheck
from compiler.tokenizer import tokenize
from compiler.parser import *
from compiler.ast import *


def build_ast(c: str) -> Expression:
    tokens = tokenize(c)
    ast = parse(tokens)
    typecheck(ast)
    return ast


def test_plusminus_simple() -> None:
    c = """
var a = 1;
a
"""
    target = Block(L, [
        VarDeclaration(L, "a",
                       Literal(L, 1, type=Int), type=Unit),
        Identifier(L, "a", type=Int),
    ], type=Int)
    assert build_ast(c) == target


def test_block_types() -> None:
    c = """
var a = 2;
if a > 1 then {
    a
}
"""
    target = Block(L, [
        VarDeclaration(L, "a", Literal(L, 2, type=Int), type=Unit),
        IfBlock(L,
                BinaryOp(L, Identifier(L, "a", type=Int),
                         ">", Literal(L, 1, type=Int), type=Bool),
                Block(L, [
                    Identifier(L, "a", type=Int),
                ], type=Int),
                None, type=Int),
    ], type=Int)
    assert build_ast(c) == target


def test_invalid_assignment() -> None:
    c = """
var a = 1;
a + 1 = 1;
"""
    with pytest.raises(Exception) as exinfo:
        build_ast(c)
    assert "variable" in str(exinfo)


def test_invalid_type() -> None:
    c = """
var a: Bool = 1;
"""
    with pytest.raises(Exception) as exinfo:
        build_ast(c)
    assert "mismatch" in str(exinfo)


def test_function_calls() -> None:
    c = """
var f: (Int) => Unit = print_int;
var b = 3;
b = f(2);
"""
    with pytest.raises(Exception) as exinfo:
        build_ast(c)
    assert "operands" in str(exinfo)
