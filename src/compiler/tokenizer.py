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


regexes = [
    ("comment", r'(#.*)|(//.*)'),
    ("multiline_comment", r'/\*[\s\S]*?\*/'),
    ("whitespace", r' +'),
    ("int_literal", r'[0-9]+'),
    ("identifier", r'[a-z_]+[a-z_1-9]*'),
    ("operator", r'((==|<=|>=|!=)|(\+|-|\*|/|<|>|=|%))'),
    ("newline", r'\n'),
    ("punctuation", r'[(){},;]'),
]

keywords = ["if", "then", "else", "while", "var"]


def tokenize(source_code: str) -> list[Token]:
    result: list[Token] = []
    line = 0
    line_start = 0
    matcher = '|'.join(f"(?P<{p[0]}>{p[1]})" for p in regexes)
    for match in re.finditer(matcher, source_code):
        match_type = match.lastgroup
        if not match_type:
            raise Exception("error")
        match match_type:
            case "whitespace":
                pass
            case "comment":
                pass
            case "newline":
                line += 1
                line_start = match.end()
            case "multiline_comment":
                line += match.group().count('\n')
                last_index = match.group().rfind('\n')
                if last_index != -1:
                    line_start = match.start() + last_index
            case "identifier":
                if match.group() in keywords:
                    match_type = "keyword"
                result.append(Token(
                    Loc(line, match.start() - line_start),
                    match_type,
                    match.group()))
            case _:
                result.append(Token(
                    Loc(line, match.start() - line_start),
                    match_type,
                    match.group()))
    return result
