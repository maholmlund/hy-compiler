from compiler.tokenizer import Token
from compiler.ast import *


def parse(tokens: list[Token]) -> Expression:
    pos = 0

    def peek() -> Token:
        if pos < len(tokens):
            return tokens[pos]
        else:
            return Token(
                tokens[-1].loc,
                "end",
                "",
            )

    def consume(expected: str | list[str] | None = None) -> Token:
        nonlocal pos
        token = peek()
        if isinstance(expected, str) and token.text != expected:
            raise Exception(f'{token.loc}: expected "{expected}"')
        if isinstance(expected, list) and token.text not in expected:
            comma_separated = ", ".join([f'"{e}"' for e in expected])
            raise Exception(
                f'{token.loc}: expected one of: {comma_separated}')
        pos += 1
        return token

    def parse_int_literal() -> Literal:
        value = consume()
        if value.type != "int_literal":
            raise Exception(f"{value.loc}: expected int literal")
        return Literal(int(value.text))

    def parse_identifier() -> Identifier:
        value = consume()
        if value.type != "identifier":
            raise Exception(f"{value.loc}: expected identifier")
        return Identifier(value.text)

    def parse_term() -> Expression:
        value = peek()
        if value.type == "identifier":
            return parse_identifier()
        elif value.type == "int_literal":
            return parse_int_literal()
        elif value.text == "(":
            return parse_parenthesized()
        else:
            raise Exception(f"{value.loc}: expected identifier or int literal")

    def parse_sum() -> Expression:
        left = parse_divmult()
        while peek().text in ['+', '-']:
            operator_token = consume(['+', '-'])
            right = parse_expression()
            left = BinaryOp(left, operator_token.text, right)
        return left

    def parse_divmult() -> Expression:
        left = parse_term()
        while peek().text in ['*', '/']:
            operator_token = consume(['*', '/'])
            right = parse_term()
            left = BinaryOp(left, operator_token.text, right)
        return left

    def parse_parenthesized() -> Expression:
        consume('(')
        result = parse_expression()
        consume(')')
        return result

    def parse_if_then_else() -> IfBlock:
        consume('if')
        condition = parse_expression()
        consume('then')
        then = parse_expression()
        if peek().text != "else":
            return IfBlock(condition, then, None)
        consume("else")
        eelse = parse_expression()
        return IfBlock(condition, then, eelse)

    def parse_expression() -> Expression:
        value = peek()
        if value.text == "if":
            return parse_if_then_else()
        return parse_sum()

    if not tokens:
        return Expression()
    result = parse_expression()
    if pos != len(tokens):
        raise Exception("expected EOF")
    return result
