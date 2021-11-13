import re
import shutil
from typing import Any
from pathlib import Path
import inspect


def _concat_split(last_symbol_in_line, replacement, source):
    return re.sub(r'(\s)*' + last_symbol_in_line + r'[\n\r](\s)*',
                  replacement, source, flags=re.MULTILINE)


def concat_split_expressions(source: str):
    source = _concat_split(r'\\', ' ', source)
    source = _concat_split(r',', ', ', source)
    return source


Source = list[str]


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


class NoTypeSpecified(Exception):
    pass


class ParsingError(Exception):
    pass


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


def gen_check_lines(param: str, base_ident_line, class_fields):
    arg_name, arg_type = parse_param(param)
    if class_fields:
        arg_name = arg_name.removeprefix('self.')
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


def gen_checks_for_params(params: Source, base_ident_line, class_fields=False):
    res = []
    for param in params:
        try:
            for check_line in gen_check_lines(param, base_ident_line, class_fields):
                res.append(check_line)
        except NoTypeSpecified:
            pass

    add_empty_line(res)
    return res


def match_signature(signature: str, line: str):
    return line.lstrip().startswith(signature)


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
        return None


def match_any_signature(sign_list, line):
    for signature in sign_list:
        if match_signature(signature, line):
            return True
    return False


def match_signature_only(signature, blacklist: list[str], line: str):
    if match_any_signature(blacklist, line):
        return False

    return match_signature(signature, line)


def transpile_funcs(source: Source):
    res = []
    for line in source:
        res.append(line)
        if match_signature_only(signature='def ', blacklist=['def __setattr__'], line=line):
            params = parse_func_definition(line)
            if params:
                res.extend(gen_checks_for_params(params, line))

    return res


def ident_is_more_or_equal(base_ident, line):
    return len(get_ident(line)) >= len(base_ident)


def is_same_block(base_ident, line):
    return ident_is_more_or_equal(base_ident, line) or line.strip() == ''


def detect_block_end(source: Source, start_line_num):
    first_line = source[start_line_num]
    increased_ident = get_increased_ident(first_line)
    line_num = start_line_num + 1

    while line_num < len(source) and is_same_block(increased_ident, source[line_num]):
        line_num += 1

    return line_num


def detect_block(source: Source, start_line_num):
    block_end_line = detect_block_end(source, start_line_num)
    block_source = source[start_line_num:block_end_line]
    return block_source, block_end_line


def __setattr__(self, name: str, value: Any) -> None:
    super().__setattr__(name, value)


def is_field(line):
    return not match_any_signature(['def', 'class'], line) \
           and re.search(r'.+:.+', line) is not None


def get_class_fields(source: Source):
    fields = []
    base_ident = get_increased_ident(source[0])

    for line in source:
        if get_ident(line) == base_ident:
            if is_field(line):
                fields.append(line)

    return fields


def get_init_fields(source: Source):
    for line_num, line in enumerate(source):
        if match_signature('def __init__', line):
            fields = []
            init_source, _ = detect_block(source, line_num)
            for line in init_source[1:]:
                if match_signature('self.', line) and is_field(line):
                    fields.append(line)
            return fields

    return []


def add_empty_line(source: Source):
    if source:
        source[-1] += '\n'


def detect_setattr(source: Source):
    for line_num, line in enumerate(source):
        if match_signature('def __setattr__', line):
            return line_num

    # else
    ident_lines = gen_lines_with_ident(source[0],
                                       inspect.getsource(__setattr__).splitlines())
    add_empty_line(ident_lines)
    insert_lines(source, 1, ident_lines)
    return 1


def transpile_class(source: Source):
    fields = get_class_fields(source)
    if init_fields := get_init_fields(source):
        fields.extend(init_fields)

    if fields:
        setattr_line_num = detect_setattr(source)

        check_lines = gen_checks_for_params(params=fields, base_ident_line=source[setattr_line_num], class_fields=True)
        insert_lines(source, setattr_line_num + 1, check_lines)

    return source


def transpile_classes(source: Source):
    res = []
    line_num = 0
    while line_num < len(source):
        line = source[line_num]
        if match_signature('class ', line):
            class_source, block_end = detect_block(source, line_num)
            class_source = transpile_class(class_source)
            res.extend(class_source)
            line_num = block_end
            continue
        else:
            res.append(line)
            line_num += 1

    return res


def transpile(source: str):
    source += '\n'
    source = source.splitlines()
    source = remove_all_comments(source)
    source = '\n'.join(source)

    source = concat_split_expressions(source)

    source = source.splitlines()

    source = transpile_classes(source)
    source = transpile_funcs(source)

    source = '\n'.join(source)

    check_func = inspect.getsource(check_type)
    source = f'{check_func}\n\n{source}'

    return source


def transpile_file(filepath: Path):
    with open(filepath, mode='r', encoding='utf8') as file:
        content = file.read()

    content = transpile(content)
    filepath = get_path_in_build(filepath)

    with open(filepath, mode='w+', encoding='utf8') as file:
        file.write(content)


def filter_files(base_directory: Path):
    res = []
    for p in base_directory.rglob('*'):
        for part in p.parts:
            if part in ignore_list:
                break
        else:
            res.append(p)
    return res


def get_build_dir():
    return BASE_DIR / BUILD_FOLDER


def get_path_in_build(filepath: Path):
    return get_build_dir() / filepath.relative_to(BASE_DIR)


def make_dir(dir_path):
    dir_path.mkdir(exist_ok=True)


def clean_any_content(folder: Path) -> None:
    for file_path in folder.iterdir():
        if file_path.is_file():
            file_path.unlink()
        elif file_path.is_dir():
            shutil.rmtree(file_path)


def transpile_project(basedir: Path):
    files = filter_files(basedir)

    for filepath in files:
        if filepath.is_dir():
            make_dir(get_path_in_build(filepath))
        else:
            if filepath.match('*.py'):
                transpile_file(filepath)
            else:
                shutil.copy2(filepath, get_path_in_build(filepath))


BUILD_FOLDER = 'build'

ignore_list = [
    BUILD_FOLDER,
    '.idea',
    'venv',
    '.git',
    '.gitignore'
]

SINGLE_IDENT = ' ' * 4


def prepare_and_transpile(base_dir):
    global BASE_DIR
    BASE_DIR = base_dir
    print(BASE_DIR)

    build_dir = get_build_dir()
    make_dir(build_dir)
    clean_any_content(build_dir)

    transpile_project(BASE_DIR)


if __name__ == '__main__':
    cur_project = Path(__file__).parent.resolve()
    bet_matcher = Path(r'/home/user/PycharmProjects/BetMatcher3/BetMatcher')

    prepare_and_transpile(cur_project)
    prepare_and_transpile(bet_matcher)
