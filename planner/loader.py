import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from planner import logger, models


def parse_recipe_file(file_path):
    file_content = Path(file_path).read_text()
    parts = map(lambda st: st.strip(), file_content.split("\n---"))
    header, items = list(
        map(lambda part: yaml.load(part, yaml.Loader), list(parts)[:2])
    )
    return header, items


def load_recipe_file(path):
    print(f"reading recipe from {path!r}")
    header, items = parse_recipe_file(path)
    recipe = models.Recipe.create(**header)
    for line in items:
        try:
            item = models.Item.create_item_from_line(line, recipe)
        except:
            print(f"could not parse item line: {line}")
            raise


def load_recipe_dir(path):
    logger.info(f"loading recipes in {path}")
    for recipe_file in Path(path).iterdir():
        load_recipe_file(recipe_file)
