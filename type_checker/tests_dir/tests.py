from typing import Any, Union

saf = str


class AttrClass:

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)


class NoTypeSpecified(Exception):
    pass


sfd = '''
adsfadf
'''


class MultiLangEvent:
    id: int
    ru_event: Union[dict, list]
    en_event: Union[dict, list]

def collection_types(ttype: tuple[int, list] = (1, 2), num: int = 0):
    pass


class Deck:
    def expression(self, a, b, c):
        if a == 5 and b is True \
                and c:
            print('passed')

    mine: int
    his: str = 's'
    all: list[int]
    simple: tuple

    def __init__(self, p: float, t: str) -> None:
        self.p: float = p
        self.t: str = t


if __name__ == '__main__':
    deck = Deck(3, [], (), 5, 'kd')
    print(deck.dict())
    deck = Deck(3, [], (), 'sf', 'kd')
