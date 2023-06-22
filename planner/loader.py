import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from planner import logger, models


def load_yaml_file(file_path):
    file_content = Path(file_path).read_text()
    parts = map(lambda st: st.strip(), file_content.split("\n---"))
    data = map(lambda part: yaml.load(part, yaml.Loader), list(parts)[:2])
    return list(data)


@dataclass
class RecipeFileData:
    header: dict
    items: list
    instructions: str


def parse_recipe_file(recipe_file_path):
    header, items, instructions = load_yaml_file(recipe_file_path)
    return RecipeFileData(header=header, items=items, instructions=instructions)


def load_recipe_file(path):
    print(f"reading recipe from {path!r}")
    file_data = parse_recipe_file(path)
    recipe = models.Recipe.create(**file_data.header)
    for line in file_data.items:
        try:
            item = models.Item.create_item_from_line(line, recipe)
        except:
            print(f"could not parse item line: {line}")
            raise


def load_recipe_dir(path):
    logger.info(f"loading recipes in {path}")
    for recipe_file in Path(path).iterdir():
        load_recipe_file(recipe_file)
