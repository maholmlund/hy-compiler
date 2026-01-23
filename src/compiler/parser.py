from compiler.tokenizer import Token
from compiler.location import L
from compiler.ast import *

# Left associative operator precedences
la_operators = [
    ["or"],
    ["and"],
    ["==", "!="],
    ["<", ">", "<=", ">="],
    ["+", "-"],
    ["/", "*", "%"],
]


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

    def parse_arg_list() -> list[Expression]:
        result = [parse_expression()]
        while peek().text == ",":
            consume(",")
            result.append(parse_expression())
        return result

    def parse_identifier_or_function() -> Expression:
        value = consume()
        if value.type != "identifier":
            raise Exception(f"{value.loc}: expected identifier")
        if peek().text != "(":
            return Identifier(value.text)
        consume("(")
        args = parse_arg_list()
        consume(")")
        return FunctionCall(value.text, args)

    def parse_term() -> Expression:
        value = peek()
        result = None
        unary = None
        if value.text in ["-", "not"]:
            unary = value.text
            consume()
        if value.type == "identifier":
            result = parse_identifier_or_function()
        elif value.type == "int_literal":
            result = parse_int_literal()
        elif value.text == "(":
            result = parse_parenthesized()
        elif value.text == "{":
            result = parse_block()
        elif value.text == "if":
            result = parse_if_then_else()
        elif value.text in ["-", "not"]:
            result = parse_term()
        else:
            raise Exception(f"{value.loc}: expected term")
        if not unary:
            return result
        return UnaryOp(unary, result)

    def parse_la_operator(level: int) -> Expression:
        if level == len(la_operators):
            return parse_term()
        left = parse_la_operator(level + 1)
        while peek().text in la_operators[level]:
            operator_token = consume(
                la_operators[level])
            right = parse_la_operator(level + 1)
            left = BinaryOp(left, operator_token.text, right)
        return left

    def parse_assignment_operator() -> Expression:
        left = parse_la_operator(0)
        if peek().text != "=":
            return left
        consume("=")
        right = parse_assignment_operator()
        return BinaryOp(left, "=", right)

    def parse_parenthesized() -> Expression:
        consume('(')
        result = parse_expression()
        consume(')')
        return result

    def parse_block() -> Block:
        expressions: list[Expression] = []
        consume("{")
        return_last = False
        while peek().text != "}":
            if peek().text == "var":
                expressions.append(parse_variable_declaration())
            else:
                expressions.append(parse_expression())
            if peek().text == "}":
                return_last = True
                break
            consume(";")
        consume("}")
        if not return_last:
            expressions.append(Expression())
        return Block(expressions)

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

    def parse_variable_declaration() -> VarDeclaration:
        consume("var")
        name = consume().text
        consume("=")
        value = parse_expression()
        return VarDeclaration(name, value)

    def parse_expression() -> Expression:
        if peek().text == "{":
            return parse_block()
        return parse_assignment_operator()

    if not tokens:
        return Expression()
    tokens.append(Token(L, "punctuation", "}"))
    tokens.insert(0, Token(L, "punctuation", "{"))
    result = parse_expression()
    if pos != len(tokens):
        raise Exception("expected EOF")
    return result
