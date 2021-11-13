from typing import Any

saf = str


class AttrClass:

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)


class NoTypeSpecified(Exception):
    pass


class Deck:
    mine: int
    his: str
    all: list[int]
    simple: tuple
