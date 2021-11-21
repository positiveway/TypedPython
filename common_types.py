SINGLE_IDENT = ' ' * 4

Source = list[str]

Fields = list[tuple[str, str]]


class NoTypeSpecified(Exception):
    pass


class ParsingError(Exception):
    pass
