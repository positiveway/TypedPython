import shutil
from pathlib import Path
from common.parsing import full_transpile


def transpile_file(source_path: Path, dest_path: Path, transpile_func):
    with open(source_path, mode='r', encoding='utf8') as file:
        content = file.read()

    content = full_transpile(content, transpile_func)

    with open(dest_path, mode='w+', encoding='utf8') as file:
        file.write(content)


def transpile_file_to_build(filepath: Path, transpile_func):
    dest_path = get_path_in_build(filepath)
    transpile_file(filepath, dest_path, transpile_func)


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


def transpile_project(basedir: Path, transpile_func):
    files = filter_files(basedir)

    for filepath in files:
        if filepath.is_dir():
            make_dir(get_path_in_build(filepath))
        else:
            if filepath.match('*.py'):
                transpile_file_to_build(filepath, transpile_func)
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


def define_base_dir(base_dir):
    global BASE_DIR
    BASE_DIR = base_dir
    print(BASE_DIR)


def prepare_and_transpile(base_dir, transpile_func):
    define_base_dir(base_dir)

    build_dir = get_build_dir()
    make_dir(build_dir)
    clean_any_content(build_dir)

    transpile_project(BASE_DIR, transpile_func)
