import re
from dataclasses import dataclass
from pathlib import Path

import yaml

import models


@dataclass
class ItemData:
    name: str
    number: int
    unit: str


def parse_item_line(line):
    quantity, name = line.split()
    number, unit = re.match(r"(\d+)\s*(\w*)", quantity).groups()
    unit = unit or None
    return ItemData(name=name, number=int(number), unit=unit)


@dataclass
class RecipeFileData:
    header: dict
    items: list
    instructions: str


def parse_recipe_file(recipe_file_path):
    file_content = Path(recipe_file_path).read_text()
    header, items, instructions = yaml.load_all(file_content, yaml.SafeLoader)
    return RecipeFileData(header=header, items=items, instructions=instructions)


def load_recipe_file(path):
    file_data = parse_recipe_file(path)
    items_data = (parse_item_line(line) for line in file_data.items)

    models.create_tables()
    recipe = models.Recipe.create(**file_data.header)
    for item_data in items_data:
        ingredient = models.Ingredient.create(name=item_data.name, unit=item_data.unit)
        models.Item.create(
            ingredient=ingredient, quantity=item_data.number, recipe=recipe
        )
