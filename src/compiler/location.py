from dataclasses import dataclass


@dataclass
class Loc:
    line: int
    column: int

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Loc):
            return False
        if id(value) == id(L) or id(self) == id(L):
            return True
        return self.line == value.line and self.column == value.column


# Dummy location, is always equal to another location. Useful in tests.
L = Loc(1, 1)
