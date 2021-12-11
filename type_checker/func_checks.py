from common.func_parsing import *


def gen_checks(params: Fields):
    check_lines = []
    for param in params:
        check_line = f'check_type("{param.name}", {param.name}, {param.type})'
        check_lines.append(check_line)

    return check_lines


def transpile_funcs(source: Source):
    res = []
    for line in source:
        res.append(line)
        if match_signature_only(signature='def ', blacklist=['def __setattr__'], line=line):
            params = parse_func_definition(line)
            params = parse_params(params)
            if params:
                res.extend(gen_checks_for_params(params, line, gen_checks))

    return res
