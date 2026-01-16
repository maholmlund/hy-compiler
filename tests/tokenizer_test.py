from compiler.tokenizer import tokenize, Token
from compiler.location import L, Loc


sample1 = """if 3 while 4 while"""
sample2 = """32323   while #123 if while
3 if"""
sample3 = """// nothing here"""


def test_simple_parsing() -> None:
    assert tokenize(sample1) == [
        Token(L, "identifier", "if"),
        Token(L, "int_literal", "3"),
        Token(L, "identifier", "while"),
        Token(L, "int_literal", "4"),
        Token(L, "identifier", "while"),
    ]
    assert tokenize(sample2) == [
        Token(L, "int_literal", "32323"),
        Token(L, "identifier", "while"),
        Token(L, "int_literal", "3"),
        Token(L, "identifier", "if")
    ]
    assert tokenize(sample3) == []


sample4 = """if #ififi
32 43

something"""


def test_locations() -> None:
    assert tokenize(sample4) == [
        Token(Loc(0, 0), "identifier", "if"),
        Token(Loc(1, 0), "int_literal", "32"),
        Token(Loc(1, 3), "int_literal", "43"),
        Token(Loc(3, 0), "identifier", "something")
    ]


sample5 = """+ - * /
% = > < == != <= >="""


def test_operators() -> None:
    assert tokenize(sample5) == [
        Token(L, "operator", "+"),
        Token(L, "operator", "-"),
        Token(L, "operator", "*"),
        Token(L, "operator", "/"),
        Token(L, "operator", "%"),
        Token(L, "operator", "="),
        Token(L, "operator", ">"),
        Token(L, "operator", "<"),
        Token(L, "operator", "=="),
        Token(L, "operator", "!="),
        Token(L, "operator", "<="),
        Token(L, "operator", ">="),
    ]


sample6 = """((}),;"""


def test_punctuation() -> None:
    assert tokenize(sample6) == [
        Token(L, "punctuation", "("),
        Token(L, "punctuation", "("),
        Token(L, "punctuation", "}"),
        Token(L, "punctuation", ")"),
        Token(L, "punctuation", ","),
        Token(L, "punctuation", ";"),
    ]


sample7 = """
if /*kdflkjl

*/ if # /*
2"""


def test_multiline_comment() -> None:
    assert tokenize(sample7) == [
        Token(L, "identifier", "if"),
        Token(L, "identifier", "if"),
        Token(L, "int_literal", "2"),
    ]


sample8 = """
if 2 ( #soo
##)
) while while /*kjdk*/ while
;if,, 8, /*
while
*/
"""


def test_all() -> None:
    assert tokenize(sample8) == [
        Token(Loc(1, 0), "identifier", "if"),
        Token(Loc(1, 3), "int_literal", "2"),
        Token(Loc(1, 5), "punctuation", "("),
        Token(Loc(3, 0), "punctuation", ")"),
        Token(Loc(3, 2), "identifier", "while"),
        Token(Loc(3, 8), "identifier", "while"),
        Token(Loc(3, 23), "identifier", "while"),
        Token(Loc(4, 0), "punctuation", ";"),
        Token(Loc(4, 1), "identifier", "if"),
        Token(Loc(4, 3), "punctuation", ","),
        Token(Loc(4, 4), "punctuation", ","),
        Token(Loc(4, 6), "int_literal", "8"),
        Token(Loc(4, 7), "punctuation", ","),
    ]
