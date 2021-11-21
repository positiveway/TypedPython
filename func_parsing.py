from common_parsing import *


def parse_func_definition(line):
    strip_line = line.strip()
    params = re.match(r'def .+\((.*)\).*:', strip_line).group(1)
    if len(params) > 0:
        if ',' in params:
            params = params.split(',')
        else:
            params = [params]

        return params
    else:
        return []


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
