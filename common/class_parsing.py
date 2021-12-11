from common.parsing import *


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
