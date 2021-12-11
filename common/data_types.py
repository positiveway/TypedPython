SINGLE_IDENT = ' ' * 4

Source = list[str]


class Param:
    def __init__(self, name, type, value) -> None:
        self.name = name
        self.type = type
        self.value = value


Fields = list[Param]


class NoTypeSpecified(Exception):
    pass


class ParsingError(Exception):
    pass
