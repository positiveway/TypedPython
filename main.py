import re

from typing import Any


def concat_split_expressions(source: str):
    return re.sub(r'(\s)*\\[\n\r](\s)*', ' ', source, flags=re.MULTILINE)


def get_ident(line):
    res = ''
    for char in line:
        if char in r'\t\s':
            res += char
    return res


def increase_ident(ident):
    return ident + ident[0]


def get_increased_ident(line):
    return increase_ident(get_ident(line))


def gen_lines_with_ident(base_ident_line, lines):
    base_ident = get_ident(base_ident_line)
    increased_ident = get_increased_ident(base_ident)
    res = [f'{base_ident}{lines[0]}']
    if len(lines) > 1:
        for line in lines[1:]:
            res.append(f'{increased_ident}{line}')
    return res


def insert_lines(source: list[str], index: int, lines):
    for line_ind, line in enumerate(lines):
        source.insert(index + line_ind, line)


def get_base_type(arg_type: str):
    if '[' in arg_type:
        return arg_type[:arg_type.find('[')]


def parse_param(param: str):
    arg_name, arg_type = param.split(':')
    if '=' in arg_type:
        arg_type = arg_type.split('=')[0]

    arg_name, arg_type = arg_name.strip(), arg_type.strip()
    arg_type = get_base_type(arg_type)
    return arg_name, arg_type


def gen_check_lines(param: str, base_ident_line):
    arg_name, arg_type = parse_param(param)
    check_lines = gen_lines_with_ident(base_ident_line, [
        f'if not isinstance({arg_name},{arg_type}):',
        f'raise TypeError("{arg_name} type is not {arg_type}")'
    ])
    return check_lines


def gen_checks_for_params(params: list[str], base_ident_line):
    res = []
    for param in params:
        for check_line in gen_check_lines(param, base_ident_line):
            res.append(check_line)
    return res


def transpile_funcs(source: list[str]):
    res = []
    for line in source:
        res.append(line)
        if line.lstrip().startswith('def'):
            params = re.match(r'def\((.)*\):', line).group(1)
            params = params.split(',')
            res.extend(gen_checks_for_params(params, line))

    return res


def detect_block_end(source: list[str], start_line_num):
    first_line = source[start_line_num]
    increased_ident = get_increased_ident(first_line)
    line_num = start_line_num + 1
    while line_num < len(source) and get_ident(source[line_num]) >= increased_ident:
        line_num += 1

    return line_num


saf = str


class A:

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)


def get_class_fields(source: list[str]):
    fields = []
    base_ident = get_ident(source[1])

    for line in source:
        if get_ident(line) == base_ident:
            if not line.lstrip().startswith('def') and ':' in line:
                fields.append(line)

    return fields


def detect_setattr(source: list[str]):
    for line_num, line in enumerate(source):
        line = line.strip()
        if line.startswith('def __setattr__'):
            return line_num
    else:
        ident_lines = gen_lines_with_ident(source[1], [
            'def __setattr__(self, name: str, value: Any) -> None:',
            'super().__setattr__(name, value)'
        ])
        insert_lines(source, 1, ident_lines)
        return 1


def transpile_class(source: list[str]):
    fields = get_class_fields(source)
    setattr_line_num = detect_setattr(source)

    check_lines = gen_checks_for_params(params=fields, base_ident_line=source[setattr_line_num])
    insert_lines(source, setattr_line_num + 1, check_lines)

    return source


def transpile_classes(source: list[str]):
    res = []
    line_num = 0
    while line_num < len(source):
        line = source[line_num]
        if line.lstrip().startswith('class'):
            block_end = detect_block_end(source, line_num)
            class_source = transpile_class(source[line_num:block_end])
            res.extend(class_source)
            line_num = block_end
            continue
        else:
            res.append(line)
            line_num += 1

    return res


def transpile(source: str):
    source += '\n'
    source = concat_split_expressions(source)
    source = source.splitlines()
    source = transpile_funcs(source)
    source = '\n'.join(source)
    return source


def transpile_file(filepath):
    pass
