from common_parsing import *


def remove_self_prefix(fields: Fields):
    for field in fields:
        field.name = field.name.removeprefix('self.')


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


def is_field(line):
    return not match_any_signature(['def', 'class'], line) \
           and re.search(r'.+:.+', line) is not None


def cut_class_fields(source: Source):
    res = []
    fields = []
    base_ident = get_increased_ident(source[0])

    for line in source:
        if get_ident(line) == base_ident and is_field(line):
            fields.append(line)
        else:
            res.append(line)

    return fields, res


def get_init_fields(source: Source):
    fields = []

    if (init_line_num := find_line_with_sig('def __init__', source)) is not None:
        init_source, _ = detect_block(source, init_line_num)
        for line in init_source[1:]:
            if match_signature('self.', line) and is_field(line):
                fields.append(line)

    return fields


def find_line_with_sig(signature: str, source: Source):
    for line_num, line in enumerate(source):
        if match_signature(signature, line):
            return line_num

    return None


def find_or_insert(signature: str, lines_to_insert: Source, source: Source):
    if (sig_line_num := find_line_with_sig(signature, source)) is not None:
        return sig_line_num

    # else
    return insert_pretty_lines(lines_to_insert, source)


def gen_checks(params: Fields):
    check_lines = ['from functools import partial', '{']
    for param in params:
        check_line = f'"{param.name}": partial(check_type, "{param.name}", value, {param.type}),'
        check_lines.append(check_line)

    check_lines.append('}[name]()')

    return check_lines


def add_setattr_checks(fields: Fields, source: Source):
    from injectable import __setattr__
    from inspect import getsource

    setattr_line_num = find_or_insert('def __setattr__',
                                      getsource(__setattr__).splitlines(),
                                      source)

    check_lines = gen_checks_for_params(params=fields, base_ident_line=source[setattr_line_num], gen_func=gen_checks)
    insert_lines(check_lines, source, setattr_line_num + 1)


def add_dict_method(fields: Fields, source: Source):
    def_line_index = insert_pretty_lines(['def dict(self):'], source)

    injectable_code = ['return {']
    for field in fields:
        line = f'"{field.name}": obj_to_dict(self.{field.name}),'
        injectable_code.append(line)

    injectable_code.append('}')

    insert_pretty_lines(injectable_code, source, def_line_index)


def filter_duplicate_cls_fields(class_fields: Fields, init_fields: Fields):
    init_fields_names = [init_field.name for init_field in init_fields]
    return [class_field for class_field in class_fields if class_field.name not in init_fields_names]


def split_cls_fields(class_fields: Fields):
    not_defined, pre_defined = [], []
    for class_field in class_fields:
        if class_field.value is None:
            not_defined.append(class_field)
        else:
            pre_defined.append(class_field)

    return not_defined, pre_defined


def conv_fields_to_func_sig_str(fields: Fields):
    fields_as_str = []
    for field in fields:
        fields_as_str.append(f'{field.name}: {field.type}')

    fields_as_str = ', '.join(fields_as_str)
    return fields_as_str


def find_or_insert_init(source: Source):
    init_line_num = find_or_insert('def __init__', ['def __init__(self) -> None:'], source)
    return init_line_num


def add_to_init_signature(not_defined_fields: Fields, source: Source):
    init_line_num = find_or_insert_init(source)
    line = source[init_line_num]

    fields_as_str = conv_fields_to_func_sig_str(not_defined_fields)

    self_sig = '(self'
    insert_pos = line.find(self_sig)
    insert_pos += len(self_sig)

    line = line[:insert_pos] + ', ' + fields_as_str + line[insert_pos:]
    source[init_line_num] = line


def conv_fields_to_str_definition(fields: Fields):
    fields_as_str = []
    for field in fields:
        fields_as_str.append(f'self.{field.name}: {field.type} = {field.value}')

    return fields_as_str


def get_all_fields(*args):
    all_fields = []
    for arg in args:
        all_fields.extend(arg)

    return all_fields


def add_to_init_body(not_defined: Fields, pre_defined: Fields, source: Source):
    for not_defined_field in not_defined:
        not_defined_field.value = not_defined_field.name

    all_fields = get_all_fields(not_defined, pre_defined)

    init_line_num = find_or_insert_init(source)
    fields_as_str = conv_fields_to_str_definition(all_fields)

    insert_pretty_lines(fields_as_str, source, init_line_num)


def merge_class_fields(class_fields: Fields, init_fields: Fields, source: Source):
    class_fields = filter_duplicate_cls_fields(class_fields, init_fields)
    if class_fields:
        not_defined, pre_defined = split_cls_fields(class_fields)
        if not_defined:
            add_to_init_signature(not_defined, source)
        if pre_defined:
            add_to_init_body(not_defined, pre_defined, source)

    all_fields = get_all_fields(class_fields, init_fields)
    return all_fields


def transpile_class(source: Source):
    class_fields, source = cut_class_fields(source)
    init_fields = get_init_fields(source)

    class_fields = parse_params(class_fields)
    init_fields = parse_params(init_fields)
    remove_self_prefix(init_fields)

    all_fields = merge_class_fields(class_fields, init_fields, source)

    if all_fields:
        add_setattr_checks(all_fields, source)
        add_dict_method(all_fields, source)

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
