from common.class_parsing import *

def gen_checks(params: Fields):
    check_lines = ['{']
    for param in params:
        check_line = f'"{param.name}": partial(check_type, "{param.name}", value, {param.type}),'
        check_lines.append(check_line)

    check_lines.append('}[name]()')

    return check_lines


def add_setattr_checks(fields: Fields, source: Source):
    from type_checker.injectable import __setattr__
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


