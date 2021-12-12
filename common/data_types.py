SINGLE_IDENT = ' ' * 4

Source = list[str]


class Param:
    def __init__(self, name, type, value) -> None:
        self.name: str = name
        self.type: str = type
        self.value: str = value


Fields = list[Param]


class NoTypeSpecified(Exception):
    pass


class ParsingError(Exception):
    pass
