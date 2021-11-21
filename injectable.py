def __setattr__(self, name: str, value) -> None:
    super().__setattr__(name, value)


def check_type(arg_name, value, arg_type):
    from typing import get_origin, get_args

    def check_single_value(_value, _type):
        if not isinstance(_value, _type):
            raise TypeError(f'"{arg_name}" type is not "{arg_type}"')

    collection_type = get_origin(arg_type)
    if collection_type is not None:
        check_single_value(value, collection_type)
        element_type = get_args(arg_type)

        if collection_type == dict:
            value = value.values()

        for val in value:
            check_single_value(val, element_type)
    else:
        check_single_value(value, arg_type)


# check_type('sdf', ['sf'], list)

def dict(obj, fields: list[tuple[str, str]]):
    from inspect import isclass
    for field in fields:
        field_name, field_type = field
        val = getattr(obj, field_name)


def insert_header_func(func, source):
    from inspect import getsource
    check_func = getsource(func)
    return f'{check_func}\n\n{source}'


def insert_header_funcs(source):
    funcs = [dict, check_type]
    for func in funcs:
        source = insert_header_func(func, source)

    return source
