def __setattr__(self, name: str, value) -> None:
    super().__setattr__(name, value)


def check_type(arg_name, value, arg_type):
    from typing import get_origin, get_args

    def check_single_value(_value, _type):
        error = TypeError(f'"{arg_name}" type is not "{arg_type}"')
        if _type in [float, int]:
            try:
                _value = _type(_value)
            except (TypeError, ValueError):
                raise error

        elif not isinstance(_value, _type):
            raise error

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

def obj_to_dict(obj):
    from inspect import isclass
    from typing import get_origin

    if isclass(obj):
        return obj.dict()
    else:
        collection_type = get_origin(type(obj))
        if collection_type is None:
            return obj
        else:
            if collection_type == dict:
                res = {}
                for key, val in obj:
                    res[key] = obj_to_dict(val)
                return res

            else:
                res = []
                for val in obj:
                    res.append(obj_to_dict(val))
                return res


def insert_header_func(func, source):
    from inspect import getsource
    check_func = getsource(func)
    return f'{check_func}\n\n{source}'


def insert_header_funcs(source):
    funcs = [obj_to_dict, check_type]
    for func in funcs:
        source = insert_header_func(func, source)

    return source
