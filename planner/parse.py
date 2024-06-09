import re
from dataclasses import dataclass
from enum import StrEnum, auto
from pathlib import Path
from typing import Any, Self

import funcy
import yaml

from planner import logger, models
from planner.errors import ParsingError

# ------------------------- ingredients -------------------------


# def load_ingredients_from_file(file_path) -> None:
#     logger.info(f"loading ingredients from file {file_path}")
#     ingredient_data = list(yaml.load_all(Path(file_path).open(), Loader=yaml.Loader))
#     logger.info(f"file contains {len(ingredient_data)} ingredients")
#     with db.atomic():
#         for d in ingredient_data:
#             models.Ingredient.create(**d)


# ------------------------- recipe item -------------------------



class Unit(StrEnum):
    KILOGRAM = auto()
    LITER = auto()
    UNIT = auto()
    TEASPOON =auto()
    TABLESPOON =auto()



@dataclass
class Quantity:
    number:int
    unit:Unit

    def __repr__(self):
        return f"Quantity({self.number},Unit.{self.unit.upper()})"

    @classmethod
    def from_tuple(cls,number:int|None,unit_string:str|None)->Self:
        # breakpoint()
        if not isinstance(number,(int,float)):
            raise ValueError(f'not a number {number}')
        match unit_string:
            case "g"|"gram"|"grams":
                return cls(number * 1e-3, Unit.KILOGRAM)
            case "kg"|"kilo"|"kilos"|"kilograms":
                return cls(number , Unit.GRAM)
            case "ml"|"mililiter"|"mililiters":
                return cls(number * 1e-3, Unit.LITER)
            case "cl"|"centiliter"|"centiliters":
                return cls(number * 1e-2, Unit.LITER)
            case "dl"|"deciliter"|"deciliters":
                return cls(number * 1e-1, Unit.LITER)
            case "l"|"liter"|"liters":
                return cls(number, Unit.LITER)
            case None|""|"u"|"unit"|"units":
                return cls(number, Unit.UNIT)
            case "tbsp"|"tablespoon"|"tablespoons":
                return cls( number, Unit.TABLESPOON)
            case "tsp"|"teaspoon"|"teaspoons":
                return cls( number, Unit.TEASPOON)
            case _:
                raise ParsingError(f"unrecognized unit: {unit_string}")


def _parse_item_line(line):
    """Parse elements out of an item line from a recipe file"""
    # pre-process
    line = line.lower()
    line = re.sub(r"\s+", " ", line)  # conpact spaces
    line = line.strip()  # remove border spaces

    # regexes
    UNIT_SYMBOLS = ["g", "kg", "L", "l", "ml", "cl", "tsp", "tbsp","unit"]
    UNIT_SYMBOL_REGEX = f"({'|'.join(UNIT_SYMBOLS)})"
    NUMBER_REGEX = r"[\d\.]+"
    QUANTITY_REGEX = NUMBER_REGEX + r"\s?" + f"{UNIT_SYMBOL_REGEX}?" + r"(?=\s)"
    PARENTHESIS_REGEX = r"\((.*)\)"

    # extract quantity
    res = re.search(QUANTITY_REGEX, line)
    if res is not None:
        quantity = res.group()
        rest = line[res.end() :].strip()
    else:
        raise ParsingError(f"quantity string not found in {line!r}")
    # extract number
    res = re.search(NUMBER_REGEX, quantity)
    number = float(res.group())
    unit = quantity[res.end() :].strip() or None

    if number == 0:
        raise ParsingError(f"parsed number is zero in line {line}")

    # extract parenthesis
    res = re.search(PARENTHESIS_REGEX, rest)
    if res is not None:
        ingredient = rest[: res.start()].strip()
    else:
        ingredient = rest
    quantity = Quantity.from_tuple(number, unit)
    return quantity,ingredient

# ------------------------- recipe file -------------------------

def _split_recipe_file(
    file_path,
) -> tuple[str, Any, Any, Any | None]:
    """Parse sections from a recipe file

    ```recipe file format
    header
    ---
    items
    ---
    [instructions]
    ```

    - header and items are yaml format
    - instructions are plain text and optional

    """
    file_ = Path(file_path)
    name = file_.stem
    file_content = file_.read_text()
    parts = [section.strip() for section in file_content.split("\n---")]
    header = parts[0]
    items = parts[1]
    try:
        instructions = parts[2]
    except IndexError:
        instructions = None
    return name, header, items, instructions


load_yaml=funcy.partial(yaml.load,Loader=yaml.Loader)


def parse_recipe_file(
    file_path,
) -> tuple[str, Any, Any, Any | None]:
    """Parse sections from a recipe file

    ```recipe file format
    header
    ---
    items
    ---
    [instructions]
    ```

    - header and items are yaml format
    - instructions are plain text and optional

    """
    name, header, items, instructions = _split_recipe_file(file_path)
    header = load_yaml(header)
    item_lines = load_yaml(items)
    items = funcy.lmap(_parse_item_line,item_lines)
    return name, header, items, instructions


# def load_recipe_dir(path) -> None:
#     """Loads all recipe files in a directory"""
#     logger.info(f"loading recipe directory: {str(path)!r}")
#     for recipe_file in Path(path).iterdir():
#         load_recipe_file(recipe_file)


# ------------------------- project -------------------------


def load_project_file(path):
    file_ = Path(path)
    project_data = yaml.load(file_.read_text(), yaml.Loader)
    project = models.Project.create(name=file_.stem, servings=project_data["servings"])
    for recipe_name in project_data["recipes"]:
        recipe = models.Recipe.get(name=recipe_name)
        models.ProjectItem.create(project=project, recipe=recipe)
    return project


# ------------------------- IO -------------------------


def dump_ingredients(file_path) -> None:
    logger.info(f"writing ingredients in {file_path!r}")
    serialized = [ingredient.dump() for ingredient in models.Ingredient.select()]
    yaml.dump_all(serialized, Path(file_path).open("w"))