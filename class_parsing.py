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


def get_class_fields(source: Source):
    fields = []
    base_ident = get_increased_ident(source[0])

    for line in source:
        if get_ident(line) == base_ident:
            if is_field(line):
                fields.append(line)

    return fields


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


def find_or_insert(signature: str, lines_to_insert: Source, source: Source, insert_at_ind=1):
    if (sig_line_num := find_line_with_sig(signature, source)) is not None:
        return sig_line_num

    # else
    return insert_pretty_lines(lines_to_insert, source, insert_at_ind)


def add_setattr_checks(fields: Fields, source: Source):
    from injectable import __setattr__
    from inspect import getsource

    setattr_line_num = find_or_insert('def __setattr__',
                                      getsource(__setattr__).splitlines(),
                                      source)

    check_lines = gen_checks_for_params(params=fields, base_ident_line=source[setattr_line_num], class_fields=True)
    insert_lines(check_lines, source, setattr_line_num + 1)


def add_dict_method(fields: Fields, source: Source):
    def_line_index = insert_pretty_lines(['def dict(self):'], source)

    injectable_code = ['return {']
    for field in fields:
        line = f'"{field.name}": obj_to_dict(self.{field.name}),'
        injectable_code.append(line)

    injectable_code.append('}')

    insert_pretty_lines(injectable_code, source, def_line_index + 1)


def transpile_class(source: Source):
    fields = get_class_fields(source)
    fields.extend(get_init_fields(source))

    fields = parse_params(fields)
    remove_self_prefix(fields)

    if fields:
        add_setattr_checks(fields, source)
        add_dict_method(fields, source)

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
