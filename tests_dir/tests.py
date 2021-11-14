from typing import Any

saf = str


class AttrClass:

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)


class NoTypeSpecified(Exception):
    pass


sfd = '''
adsfadf
'''


class Deck:
    def expression(self, a, b, c):
        if a == 5 and b is True \
                and c:
            print('passed')

    mine: int
    his: str
    all: list[int]
    simple: tuple

    def __init__(self, p: float, t: str) -> None:
        self.p: float = p
        self.t: str = t
