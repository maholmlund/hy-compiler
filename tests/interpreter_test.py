import pytest

from compiler.tokenizer import tokenize
from compiler.parser import parse
from compiler.interpreter import interpret


def run_code(src: str) -> int | bool | None:
    tokens = tokenize(src)
    ast = parse(tokens)
    return interpret(ast)


def test_math() -> None:
    c = """1+2+3*2"""
    assert run_code(c) == 9


def test_shadowing() -> None:
    c = """
var a = 6;
{var a = 7}
a"""
    assert run_code(c) == 6


def test_fibonacci() -> None:
    c = """
# calculate sum of 10 first fibonacci numbers
var sum = 0;
var last1 = 1;
var last2 = 0;
var c = 0;
while c < 9 do {
    sum = sum + last1;
    c = c + 1;
    var tmp = last1 + last2;
    last2 = last1;
    last1 = tmp;
}
sum
"""
    assert run_code(c) == 88


def test_cursed_code() -> None:
    c = """
if false then 1 else 1 + {1} 5"""
    assert run_code(c) == 5


def test_collatz_conjecture() -> None:
    c = """
var i = 27;
var c = 0;
while i != 1 do {
    c = c + 1;
    if i % 2 == 0 then {
        i = i / 2;
    } else {
        i = 3 * i + 1;
    }
}
c
"""
    assert run_code(c) == 111


def test_num_primality() -> None:
    c = """
var n = 83;
var devisor = n / 2;
var is_prime = true;
while devisor != 1 do {
    if n % devisor == 0 then is_prime = false;
    devisor = devisor - 1; # this is a comment
}
is_prime
"""
    assert run_code(c) == True


def test_sum_of_numbers() -> None:
    c = """
var num = 1659327469345786762;
var sum = 0;
while num > 0 do {
    var digit = num % 10;
    sum = sum + digit;
    num = num / 10;
}
sum
"""
    assert run_code(c) == 100
