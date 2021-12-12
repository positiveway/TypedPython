from common.class_parsing import transpile_classes
from type_checker.class_checks import transpile_class
from type_checker.func_checks import transpile_funcs
from pathlib import Path


def transpile(source: str):
    source = source.splitlines()

    source = transpile_classes(source, transpile_class)
    source = transpile_funcs(source)

    source = '\n'.join(source)
    source += '\n'

    from type_checker.injectable import insert_header_funcs
    source = insert_header_funcs(source)

    return source


if __name__ == '__main__':
    cur_project = Path(__file__).parent.resolve()
    bet_matcher = Path(r'/home/user/PycharmProjects/BetMatcher3/BetMatcher')
    tests_only_dir = cur_project / 'tests_dir'

    from common.files_ops import prepare_and_transpile

    prepare_and_transpile(cur_project, transpile)
    prepare_and_transpile(bet_matcher, transpile)
