from dataclasses import dataclass
from typing import Self
from compiler.ast import *


@dataclass
class SymTab[T]:
    parent: Self | None
    symbols: dict[str, T]

    def _search(self, name: str) -> None | T:
        result = None
        current: SymTab | None = self
        while current is not None:
            if name in current.symbols:
                result = current.symbols[name]
                break
            current = current.parent
        return result

    def find(self, name: str) -> None | T:
        return self._search(name)

    def require(self, name: str) -> T:
        result = self._search(name)
        if result is None:
            raise Exception(f"Could not find symbol {name}")
        return result


global_symbols: dict[str, Type] = {
    '+': FunType([Int, Int], Int),
    '-': FunType([Int, Int], Int),
    '*': FunType([Int, Int], Int),
    '/': FunType([Int, Int], Int),
    '%': FunType([Int, Int], Int),
    'and': FunType([Int, Int], Bool),
    'or': FunType([Int, Int], Bool),
    '<=': FunType([Int, Int], Bool),
    '>=': FunType([Int, Int], Bool),
    '>': FunType([Int, Int], Bool),
    '<': FunType([Int, Int], Bool),
    'print_int': FunType([Int], Unit),
    'print_bool': FunType([Bool], Unit),
    'read_int': FunType([], Int),
}
