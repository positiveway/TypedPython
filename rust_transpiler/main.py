from pathlib import Path
from common.class_parsing import *
from common.files_ops import define_base_dir, get_build_dir, make_dir, clean_any_content


def transpile(source: str):
    source = source.splitlines()

    source = transpile_classes(source, transpile_class)
    return final_join_source(source)


def main():
    bet_matcher = Path(r'/home/user/PycharmProjects/BetMatcher3/BetMatcher')

    from common.files_ops import prepare_and_transpile

    prepare_and_transpile(bet_matcher, transpile)


# FIXME
def transpile_class(source: Source):
    definition = source[0].lstrip('class ').rstrip(':')
    res = []
    # if model class
    if '(' in definition:
        new_def = 'enum ' + definition.split('(')[0]
        for line in source[1:]:
            enum_val = line.split('=')[0].strip().capitalize()
            res.append(enum_val)
    else:
        class_fields, source = cut_class_fields(source)
        class_fields = parse_params(class_fields)

        new_def = 'struct ' + definition
        for field in class_fields:
            field.type = field.type.capitalize()

            if field.value == 'None':
                field.type = f'Option<{field.type}>'

            rust_field = field.name + ': ' + field.type
            res.append(rust_field)

    for ind, line in enumerate(res):
        res[ind] = SINGLE_IDENT + line + ','
    new_def += ' {'
    res.insert(0, new_def)
    res.append('}')
    return res


def complete_block(new_def, res):
    for ind, line in enumerate(res):
        res[ind] = SINGLE_IDENT + line + ','
    new_def += ' {'
    res.insert(0, new_def)
    res.append('}')
    return res


def convert_enum(source: Source) -> Source:
    definition = source[0].lstrip('class ').rstrip(':')
    res = []

    new_def = 'enum ' + definition.split('(')[0]
    for line in source[1:]:
        enum_val = line.split('=')[0].strip().capitalize()
        res.append(enum_val)

    return complete_block(new_def, res)


def convert_lines(source: str):
    source = source.splitlines()

    source = convert_enum(source)

    return final_join_source(source)


def convert():
    cur_project = Path(__file__).parent.resolve()
    define_base_dir(cur_project)

    build_dir = get_build_dir()
    make_dir(build_dir)
    clean_any_content(build_dir)

    input_file = cur_project / 'input.py'
    output_file = cur_project / build_dir / 'input.rs'

    from common.files_ops import transpile_file
    transpile_file(input_file, output_file, convert_lines)


if __name__ == '__main__':
    convert()
