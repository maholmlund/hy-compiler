import pytest

from compiler.parser import parse
from compiler.tokenizer import Token
from compiler.location import L
from compiler.ast import *


def test_plusminus_simple() -> None:
    tokens = [
        Token(L, "int_literal", "2"),
        Token(L, "operator", "+"),
        Token(L, "int_literal", "3"),
    ]
    assert parse(tokens) == Block([BinaryOp(Literal(2), '+', Literal(3))])


def test_plusminus_multiple() -> None:
    tokens = [
        Token(L, "int_literal", "1"),
        Token(L, "operator", "+"),
        Token(L, "int_literal", "2"),
        Token(L, "operator", "-"),
        Token(L, "int_literal", "3"),
        Token(L, "operator", "+"),
        Token(L, "int_literal", "4"),
    ]
    assert parse(tokens) == Block([BinaryOp(BinaryOp(
        BinaryOp(Literal(1), '+', Literal(2)), '-', Literal(3)), '+', Literal(4))])


def test_plusminus_invalid_syntax() -> None:
    tokens = [
        Token(L, "int_literal", "1"),
        Token(L, "operator", "+"),
        Token(L, "operator", "+"),
        Token(L, "int_literal", "1"),
    ]
    with pytest.raises(Exception) as exinfo:
        parse(tokens)
    assert "term" in str(exinfo)


def test_precedence() -> None:
    tokens = [
        Token(L, "int_literal", "1"),
        Token(L, "operator", "+"),
        Token(L, "int_literal", "2"),
        Token(L, "operator", "*"),
        Token(L, "int_literal", "3"),
    ]
    assert parse(tokens) == Block([BinaryOp(Literal(1), '+',
                                            BinaryOp(Literal(2), '*', Literal(3)))])


def test_assignment_precedence() -> None:
    tokens = [
        Token(L, "int_literal", "1"),
        Token(L, "operator", "+"),
        Token(L, "int_literal", "2"),
        Token(L, "operator", "*"),
        Token(L, "int_literal", "3"),
        Token(L, "operator", "="),
        Token(L, "int_literal", "4"),
    ]
    assert parse(tokens) == Block([BinaryOp(
        BinaryOp(
            Literal(1),
            "+",
            BinaryOp(
                Literal(2),
                "*",
                Literal(3)
            ),
        ),
        "=",
        Literal(4)
    )])


def test_parenthesis() -> None:
    tokens = [
        Token(L, "punctuation", "("),
        Token(L, "int_literal", "1"),
        Token(L, "operator", "+"),
        Token(L, "int_literal", "2"),
        Token(L, "punctuation", ")"),
        Token(L, "operator", "*"),
        Token(L, "int_literal", "3"),
    ]
    assert parse(tokens) == Block([BinaryOp(
        BinaryOp(Literal(1), '+', Literal(2)), '*', Literal(3))])


def test_complex_math() -> None:
    # 1+((2*3-4)-2)*2
    tokens = [
        Token(L, "int_literal", "1"),
        Token(L, "operator", "+"),
        Token(L, "punctuation", "("),
        Token(L, "punctuation", "("),
        Token(L, "int_literal", "2"),
        Token(L, "operator", "*"),
        Token(L, "int_literal", "3"),
        Token(L, "operator", "-"),
        Token(L, "int_literal", "4"),
        Token(L, "punctuation", ")"),
        Token(L, "operator", "-"),
        Token(L, "int_literal", "2"),
        Token(L, "punctuation", ")"),
        Token(L, "operator", "*"),
        Token(L, "int_literal", "2"),
    ]
    assert parse(tokens) == Block([BinaryOp(
        Literal(1),
        '+',
        BinaryOp(
            BinaryOp(
                BinaryOp(
                    BinaryOp(
                        Literal(2),
                        '*',
                        Literal(3)
                    ),
                    '-',
                    Literal(4)
                ),
                '-',
                Literal(2)
            ),
            '*',
            Literal(2)
        )
    )])


def test_unary_operator_chaining() -> None:
    tokens = [
        Token(L, "operator", "-"),
        Token(L, "operator", "-"),
        Token(L, "operator", "not"),
        Token(L, "int_literal", "4"),
    ]
    assert parse(tokens) == Block([UnaryOp(
        "-", UnaryOp("-", UnaryOp("not", Literal(4))))])


def test_unmatched_parenthesis() -> None:
    tokens = [
        Token(L, "punctuation", "("),
        Token(L, "punctuation", "("),
        Token(L, "punctuation", "("),
        Token(L, "int_literal", "2"),
        Token(L, "punctuation", ")"),
        Token(L, "punctuation", ")"),
    ]
    with pytest.raises(Exception) as exinfo:
        parse(tokens)
    assert ")" in str(exinfo)


def test_extra_tokens() -> None:
    tokens = [
        Token(L, "int_literal", "1"),
        Token(L, "operator", "+"),
        Token(L, "int_literal", "2"),
        Token(L, "punctuation", ")"),
    ]
    with pytest.raises(Exception) as exinfo:
        parse(tokens)
    assert ";" in str(exinfo)


def test_no_tokens() -> None:
    tokens: list[Token] = []
    assert parse(tokens) == Expression()


def test_missing_identifier() -> None:
    tokens = [
        Token(L, "punctuation", "("),
        Token(L, "int_literal", "1"),
        Token(L, "operator", "+"),
        Token(L, "punctuation", ")"),
    ]
    with pytest.raises(Exception) as exinfo:
        parse(tokens)
    assert "term" in str(exinfo)


def test_if() -> None:
    tokens = [
        Token(L, "keyword", "if"),
        Token(L, "int_literal", "1"),
        Token(L, "keyword", "then"),
        Token(L, "int_literal", "2"),
    ]
    assert parse(tokens) == Block([IfBlock(Literal(1), Literal(2), None)])


def test_if_else() -> None:
    tokens = [
        Token(L, "keyword", "if"),
        Token(L, "int_literal", "1"),
        Token(L, "keyword", "then"),
        Token(L, "int_literal", "2"),
        Token(L, "keyword", "else"),
        Token(L, "int_literal", "3"),
    ]
    assert parse(tokens) == Block(
        [IfBlock(Literal(1), Literal(2), Literal(3))])


def test_if_as_part_of_expression() -> None:
    tokens = [
        Token(L, "int_literal", "0"),
        Token(L, "operator", "+"),
        Token(L, "keyword", "if"),
        Token(L, "int_literal", "1"),
        Token(L, "keyword", "then"),
        Token(L, "int_literal", "2"),
        Token(L, "keyword", "else"),
        Token(L, "int_literal", "3"),
    ]
    assert parse(tokens) == Block([BinaryOp(Literal(0), '+',
                                            IfBlock(Literal(1), Literal(2), Literal(3)))])


def test_nested_if() -> None:
    tokens = [
        Token(L, "keyword", "if"),
        Token(L, "int_literal", "1"),
        Token(L, "keyword", "then"),
        Token(L, "punctuation", "("),
        Token(L, "keyword", "if"),
        Token(L, "int_literal", "1"),
        Token(L, "keyword", "then"),
        Token(L, "int_literal", "2"),
        Token(L, "punctuation", ")"),
        Token(L, "keyword", "else"),
        Token(L, "int_literal", "3"),
    ]
    assert parse(tokens) == Block([IfBlock(Literal(1), IfBlock(
        Literal(1), Literal(2), None), Literal(3))])


def test_function() -> None:
    tokens = [
        Token(L, "identifier", "foo"),
        Token(L, "punctuation", "("),
        Token(L, "int_literal", "1"),
        Token(L, "punctuation", ","),
        Token(L, "int_literal", "2"),
        Token(L, "punctuation", ")"),
    ]
    assert parse(tokens) == Block(
        [FunctionCall("foo", [Literal(1), Literal(2)])])


def test_nested_functions() -> None:
    tokens = [
        Token(L, "identifier", "foo"),
        Token(L, "punctuation", "("),
        Token(L, "identifier", "bar"),
        Token(L, "punctuation", "("),
        Token(L, "int_literal", "3"),
        Token(L, "punctuation", ")"),
        Token(L, "punctuation", ","),
        Token(L, "int_literal", "1"),
        Token(L, "punctuation", ","),
        Token(L, "int_literal", "2"),
        Token(L, "punctuation", ","),
        Token(L, "identifier", "bar"),
        Token(L, "punctuation", "("),
        Token(L, "int_literal", "4"),
        Token(L, "punctuation", ")"),
        Token(L, "punctuation", ")"),
    ]
    assert parse(tokens) == Block([FunctionCall(
        "foo",
        [
            FunctionCall(
                "bar",
                [Literal(3)]
            ),
            Literal(1),
            Literal(2),
            FunctionCall(
                "bar",
                [Literal(4)]
            )
        ]
    )])


def test_missing_argument() -> None:
    tokens = [
        Token(L, "identifier", "foo"),
        Token(L, "punctuation", "("),
        Token(L, "int_literal", "1"),
        Token(L, "punctuation", ","),
        Token(L, "punctuation", ")"),
    ]
    with pytest.raises(Exception) as exinfo:
        parse(tokens)
    assert "term" in str(exinfo)


def test_block_with_return_value() -> None:
    tokens = [
        Token(L, "identifier", "a"),
        Token(L, "operator", "="),
        Token(L, "punctuation", "{"),
        Token(L, "identifier", "f"),
        Token(L, "punctuation", "("),
        Token(L, "int_literal", "1"),
        Token(L, "punctuation", ")"),
        Token(L, "punctuation", ";"),
        Token(L, "identifier", "a"),
        Token(L, "punctuation", "}"),
    ]
    assert parse(tokens) == Block([
        BinaryOp(
            Identifier("a"),
            "=",
            Block([
                FunctionCall(
                    "f",
                    [Literal(1)]
                ),
                Identifier("a")
            ])
        )
    ])


def test_missing_semicolon() -> None:
    tokens = [
        Token(L, "identifier", "f"),
        Token(L, "operator", "+"),
        Token(L, "int_literal", "1"),
        Token(L, "identifier", "p"),
    ]
    with pytest.raises(Exception) as exinfo:
        parse(tokens)
    assert ";" in str(exinfo)


def test_return_none() -> None:
    tokens = [
        Token(L, "identifier", "f"),
        Token(L, "operator", "+"),
        Token(L, "int_literal", "1"),
        Token(L, "punctuation", ";"),
    ]
    assert parse(tokens) == Block(
        [BinaryOp(Identifier("f"), "+", Literal(1)), Expression()])


def test_more_complex_block() -> None:
    tokens = [
        Token(L, "identifier", "f"),
        Token(L, "operator", "+"),
        Token(L, "int_literal", "1"),
        Token(L, "punctuation", ";"),
        Token(L, "punctuation", "{"),
        Token(L, "int_literal", "1"),
        Token(L, "punctuation", ";"),
        Token(L, "int_literal", "1"),
        Token(L, "punctuation", ";"),
        Token(L, "punctuation", "{"),
        Token(L, "punctuation", "}"),
        Token(L, "punctuation", "}"),
    ]
    assert parse(tokens) == Block([
        BinaryOp(Identifier("f"), "+", Literal(1)),
        Block([
            Literal(1),
            Literal(1),
            Block([Expression()])
        ])
    ])
