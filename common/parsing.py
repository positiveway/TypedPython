import re
from common.data_types import *


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


def get_increased_ident(line):
    return get_ident(line) + SINGLE_IDENT


def get_decreased_ident(line):
    return get_ident(line).removesuffix(SINGLE_IDENT)


def gen_lines_with_ident(base_ident_line, lines):
    ident = get_increased_ident(base_ident_line)
    res = []
    for line in lines:
        if match_signature('if', line):
            res.append(f'{ident}{line}')
            ident = get_increased_ident(ident)
            continue

        if '{' in line and '}' not in line:
            res.append(f'{ident}{line}')
            ident = get_increased_ident(ident)
            continue

        if '}' in line and '{' not in line:
            ident = get_decreased_ident(ident)
            res.append(f'{ident}{line}')
            continue

        res.append(f'{ident}{line}')

    return res


def insert_lines(lines: Source, source: Source, insert_after_line: int):
    insert_at_ind = insert_after_line + 1
    for line_ind, line in enumerate(lines):
        source.insert(insert_at_ind + line_ind, line)

    return insert_at_ind


def insert_pretty_lines(lines_to_insert: Source, source: Source, insert_after_line=0):
    line_before_insertion = source[insert_after_line]
    ident_lines = gen_lines_with_ident(line_before_insertion, lines_to_insert)
    add_empty_line(ident_lines)
    return insert_lines(ident_lines, source, insert_after_line)


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
        arg_type, arg_value = arg_type.split('=')
        arg_value = arg_value.strip()
    else:
        arg_value = None

    arg_name = arg_name.strip()
    arg_type = arg_type.strip()

    if not arg_name:
        raise ParsingError('Argument name is empty')

    if not arg_type:
        raise ParsingError('Argument type is empty')

    return Param(arg_name, arg_type, arg_value)


def parse_params(params: list[str]) -> list[Param]:
    parsed_params = []
    for param in params:
        try:
            parsed_params.append(parse_param(param))
        except NoTypeSpecified:
            pass

    return parsed_params


def gen_checks_for_params(params: Fields, base_ident_line, gen_func):
    check_lines = gen_func(params)
    check_lines = gen_lines_with_ident(base_ident_line, check_lines)
    add_empty_line(check_lines)

    return check_lines


def match_signature(signature: str, line: str):
    return line.lstrip().startswith(signature)


def r_match_signature(signature: str, line: str):
    return line.rstrip().endswith(signature)


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
    if len(source) > 1:
        source[-1] += '\n'


def preprocess_clean(source: str):
    source += '\n'
    source = source.splitlines()
    source = remove_all_comments(source)
    source = '\n'.join(source)

    source = concat_split_expressions(source)

    return source


def final_join_source(source: Source):
    source = '\n'.join(source)
    source += '\n'
    return source


def full_transpile(source: str, transpile_func):
    source = preprocess_clean(source)
    source = transpile_func(source)
    return source
