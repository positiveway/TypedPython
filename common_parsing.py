import re
from common_types import *


def _concat_split(last_symbol_in_line, replacement, source):
    return re.sub(r'(\s)*' + last_symbol_in_line + r'[\n\r](\s)*',
                  replacement, source, flags=re.MULTILINE)


def concat_multiline_strings(source: str):
    re_multiline = re.compile("\'\'\'.*\'\'\'", flags=re.MULTILINE | re.DOTALL)
    while match := re_multiline.search(source):
        content = match.group(0)
        content = re.sub('\n', '\\n', content)
        content = re.sub(r"'''", r"'", content)
        source = re_multiline.sub(content, source)

    return source


def concat_split_expressions(source: str):
    source = _concat_split(r'\\', ' ', source)
    source = _concat_split(r',', ', ', source)
    # source = concat_multiline_strings(source)
    return source


def get_ident(line):
    ident_len = len(line) - len(line.lstrip())
    return line[:ident_len]


def increase_ident(ident):
    return ident + SINGLE_IDENT


def get_increased_ident(line):
    return increase_ident(get_ident(line))


def gen_lines_with_ident(base_ident_line, lines):
    base_ident = get_increased_ident(base_ident_line)
    res = []
    for line in lines:
        res.append(f'{base_ident}{line}')
        if match_signature('if ', line):
            base_ident = get_increased_ident(base_ident)

    return res


def insert_lines(source: Source, index: int, lines):
    for line_ind, line in enumerate(lines):
        source.insert(index + line_ind, line)


def remove_comment_lines(source: Source):
    res = []
    for line in source:
        if not line.lstrip().startswith('#'):
            res.append(line)

    return res


def remove_endline_comments(source: Source):
    res = []
    for line in source:
        if (sharp_pos := line.rfind('#')) != -1:
            if (apos_pos := line.rfind("'")) != -1 and apos_pos > sharp_pos:
                res.append(line)
                continue
            else:
                line = line[:sharp_pos]

        res.append(line)

    return res


def remove_all_comments(source: Source):
    source = remove_comment_lines(source)
    source = remove_endline_comments(source)
    return source


def parse_param(param: str):
    if ':' not in param:
        raise NoTypeSpecified()

    arg_name, arg_type = param.split(':')
    if '=' in arg_type:
        arg_type = arg_type.split('=')[0]

    arg_name, arg_type = arg_name.strip(), arg_type.strip()

    if not arg_name:
        raise ParsingError('Argument name is empty')

    if not arg_type:
        raise ParsingError('Argument type is empty')

    return arg_name, arg_type


def parse_params(params: list[str]):
    parsed_params = []
    for param in params:
        try:
            arg_name, arg_type = parse_param(param)
            parsed_params.append((arg_name, arg_type))
        except NoTypeSpecified:
            pass

    return parsed_params


def gen_check_lines(arg_name: str, arg_type: str, base_ident_line, class_fields):
    if class_fields:
        check_lines = [
            f'if name == "{arg_name}":',
            f'check_type("{arg_name}", value, {arg_type})'
        ]
    else:
        check_lines = [
            f'check_type("{arg_name}", {arg_name}, {arg_type})'
        ]

    check_lines = gen_lines_with_ident(base_ident_line, check_lines)
    return check_lines


def gen_checks_for_params(params: Fields, base_ident_line, class_fields=False):
    res = []
    for param in params:
        arg_name, arg_type = param
        for check_line in gen_check_lines(arg_name, arg_type, base_ident_line, class_fields):
            res.append(check_line)

    add_empty_line(res)
    return res


def match_signature(signature: str, line: str):
    return line.lstrip().startswith(signature)


def match_any_signature(sign_list, line):
    for signature in sign_list:
        if match_signature(signature, line):
            return True
    return False


def match_signature_only(signature, blacklist: list[str], line: str):
    if match_any_signature(blacklist, line):
        return False

    return match_signature(signature, line)


def add_empty_line(source: Source):
    if source:
        source[-1] += '\n'


def transpile(source: str):
    source += '\n'
    source = source.splitlines()
    source = remove_all_comments(source)
    source = '\n'.join(source)

    source = concat_split_expressions(source)

    source = source.splitlines()

    from class_parsing import transpile_classes
    from func_parsing import transpile_funcs
    source = transpile_classes(source)
    source = transpile_funcs(source)

    source = '\n'.join(source)

    from injectable import insert_header_funcs
    source = insert_header_funcs(source)

    return source
