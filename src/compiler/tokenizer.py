import re
from dataclasses import dataclass

from compiler.location import Loc


@dataclass
class Token:
    loc: Loc
    type: str
    text: str


@dataclass
class TokenMatcher:
    regex: re.Pattern
    type: str


# regexes
identifier = TokenMatcher(re.compile(r'[a-z_]+[a-z_1-9]*'), "identifier")
literal = TokenMatcher(re.compile(r'[0-9]+'), "int_literal")
operator = TokenMatcher(re.compile(
    r'((==|<=|>=|!=)|(\+|-|\*|/|<|>|=|%))'), "operator")
punctuation = TokenMatcher(re.compile(r'[(){},;]'), "punctuation")
skip = TokenMatcher(re.compile(r'( +|#.*$|//.*$)'), "skip")


def tokenize(source_code: str) -> list[Token]:
    result: list[Token] = []
    lines = source_code.split('\n')
    for (line_n, line) in enumerate(lines):
        column = 0
        while column < len(line):
            skip_match = skip.regex.match(line, column)
            if skip_match:
                column += len(skip_match.group(0))
                continue
            found = False
            for current in [identifier, literal, operator, punctuation]:
                match = current.regex.match(line, column)
                if match:
                    result.append(
                        Token(Loc(line_n, column), current.type, match.group(0)))
                    found = True
                    column += len(match.group(0))
                    break
            if not found:
                raise Exception("invalid syntax")
            if column == len(line):
                break
    return result
