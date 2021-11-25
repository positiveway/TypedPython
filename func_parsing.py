import re

from common_parsing import *


def parse_func_definition(line):
    strip_line = line.strip()
    if re.match(r'def .+\((.*)\).*:', strip_line):
        params_line = strip_line[strip_line.find('(') + 1:strip_line.rfind(')')]
        if len(params_line) > 0:
            bracket_count = 0
            prev_cut_pos = 0
            params = []
            for ind, char in enumerate(params_line):
                if char in ['[', '(']:
                    bracket_count += 1
                elif char in [']', ')']:
                    bracket_count -= 1
                elif char == ',' and bracket_count == 0:
                    params.append(params_line[prev_cut_pos:ind])
                    prev_cut_pos = ind + 1

            params.append(params_line[prev_cut_pos:])
            return params

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
