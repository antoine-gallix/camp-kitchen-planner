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
class ItemData:
    name: str
    number: int
    unit: str


def parse_item_line(line):
    # pre-process
    line = line.lower()
    line = re.sub(r"\s+", " ", line)  # conpact spaces
    line = line.strip()  # remove border spaces

    # regexes
    UNIT_SYMBOLS = ["g", "kg", "L", "l", "ml", "cl", "tsp", "tbsp"]
    UNIT_SYMBOL_REGEX = f"({'|'.join(UNIT_SYMBOLS)})"
    QUANTITY_REGEX = r"\d+" + r"\s?" + f"{UNIT_SYMBOL_REGEX}?"
    PARENTHESIS_REGEX = r"\((.*)\)"

    # extract quantity
    res = re.search(QUANTITY_REGEX, line)
    if res is not None:
        quantity = res.group()
        rest = line[res.end() :].strip()
    else:
        raise Exception(f"quantity string not found in {line!r}")

    # extract number
    res = re.search(r"\d+", quantity)
    number = res.group()
    unit = quantity[res.end() :].strip() or None

    # extract parenthesis
    res = re.search(PARENTHESIS_REGEX, rest)
    if res is not None:
        ingredient = rest[: res.start()].strip()
    else:
        ingredient = rest
    return ItemData(name=ingredient, number=int(number), unit=unit)


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
    items_data = (parse_item_line(line) for line in file_data.items)

    models.create_tables()
    recipe = models.Recipe.create(**file_data.header)
    for item_data in items_data:
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
