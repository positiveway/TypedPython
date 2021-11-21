from pathlib import Path

if __name__ == '__main__':
    cur_project = Path(__file__).parent.resolve()
    bet_matcher = Path(r'/home/user/PycharmProjects/BetMatcher3/BetMatcher')
    tests_only_dir = cur_project / 'tests_dir'

    from files_ops import prepare_and_transpile

    prepare_and_transpile(cur_project)
    prepare_and_transpile(bet_matcher)
