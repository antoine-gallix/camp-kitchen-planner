import re
from dataclasses import dataclass
from pathlib import Path

import yaml
from icecream import ic

from planner import models


def load_yaml_file(file_path):
    file_content = Path(file_path).read_text()
    return list(yaml.load_all(file_content, yaml.SafeLoader))


@dataclass
class RecipeFileData:
    header: dict
    items: list
    instructions: str


def parse_recipe_file(recipe_file_path):
    header, items, instructions = load_yaml_file(recipe_file_path)
    return RecipeFileData(header=header, items=items, instructions=instructions)


def load_recipe_file(path):
    print(f"reading recipe from {path}")
    file_data = parse_recipe_file(path)
    recipe = models.Recipe.create(**file_data.header)
    for item_data in file_data.items:
        kwargs = {"name": item_data.name}
        if item_data.unit is not None:
            kwargs["unit"] = item_data.unit
        ingredient, _ = models.Ingredient.get_or_create(**kwargs)
        models.Item.create(
            ingredient=ingredient, quantity=item_data.number, recipe=recipe
        )


def load_recipe_dir(path):
    print(f"loading recipes in {path}")
    for recipe_file in Path(path).iterdir():
        load_recipe_file(recipe_file)
