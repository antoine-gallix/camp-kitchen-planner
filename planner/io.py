import yaml
import pathlib


def load_yaml(stream):
    return yaml.load(stream, Loader=yaml.Loader)


def load_all_yaml_from_file(file_path):
    return yaml.load_all(pathlib.Path(file_path).read_text(), Loader=yaml.Loader)
