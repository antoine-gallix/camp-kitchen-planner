import re
from dataclasses import dataclass
from pathlib import Path


import funcy
import yaml
from typing import Any
from planner import logger, models
from planner import db

# ------------------------- ingredients -------------------------


def load_ingredients_from_file(file_path) -> None:
    logger.info(f"loading ingredients from file {file_path}")
    ingredient_data = list(yaml.load_all(Path(file_path).open(), Loader=yaml.Loader))
    logger.info(f"file contains {len(ingredient_data)} ingredients")
    with db.atomic():
        for d in ingredient_data:
            models.Ingredient.create(**d)


# ------------------------- recipe -------------------------


def normalize_quantity(number, unit) -> tuple[str, float | int]:
    """Convert a quantity to the standard unit of its class"""
    match unit:
        case "mg":
            return number * 1e-6, "kg"
        case "g":
            return number * 1e-3, "kg"
        case "kg":
            return number, "kg"
        case "ml":
            return number * 1e-3, "l"
        case "cl":
            return number * 1e-2, "l"
        case "dl":
            return number * 1e-1, "l"
        case "l":
            return number, "l"
        case None:
            return number, "unit"
        case "":
            unit = number, "unit"
        case "tbsp":
            unit = number, "tbsp"
        case "tsp":
            unit = number, "tsp"
        case _:
            raise ValueError(f"unrecognized unit: {unit}")


def parse_item_line(line):
    """Parse elements out of an item line from a recipe file"""
    # pre-process
    line = line.lower()
    line = re.sub(r"\s+", " ", line)  # conpact spaces
    line = line.strip()  # remove border spaces

    # regexes
    UNIT_SYMBOLS = ["g", "kg", "L", "l", "ml", "cl", "tsp", "tbsp"]
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
        raise Exception(f"quantity string not found in {line!r}")
    # extract number
    res = re.search(NUMBER_REGEX, quantity)
    number = float(res.group())
    unit = quantity[res.end() :].strip() or None

    if number == 0:
        raise Exception(f"parsed number is zero in line {line}")

    # extract parenthesis
    res = re.search(PARENTHESIS_REGEX, rest)
    if res is not None:
        ingredient = rest[: res.start()].strip()
    else:
        ingredient = rest
    return ingredient, number, unit


def create_item_from_line(line, recipe) -> models.RecipeItem:
    name, number, unit = parse_item_line(line)
    number, unit = normalize_quantity(number, unit)
    if (
        ingredient := models.Ingredient.select()
        .where(models.Ingredient.name == name, models.Ingredient.unit == unit)
        .get_or_none()
    ):
        logger.debug("ingredient found in database")
    else:
        ingredient = models.Ingredient(name=name, unit=unit)
        logger.debug(f"new ingredient created: {ingredient}")
    item = models.RecipeItem(ingredient=ingredient, quantity=number, recipe=recipe)
    logger.debug(f"recipe item created: {item}")
    return item


def _parse_recipe_file(
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
    header = yaml.load(parts[0], yaml.Loader)
    items = yaml.load(parts[1], yaml.Loader)
    try:
        instructions = parts[2]
    except IndexError:
        instructions = None
    return name, header, items, instructions


def load_recipe_file(path) -> models.Recipe:
    """Reads a recipe file and load recipe in database"""
    logger.debug(f"loading recipe {str(path)!r}")
    name, header, items, instructions = _parse_recipe_file(path)
    with db.atomic():
        recipe = models.Recipe.create(
            name=name, serves=header["serves"], instructions=instructions
        )
        for line in items:
            try:
                item = models.RecipeItem.create_item_from_line(line, recipe)
            except:
                logger.debug(f"could not parse item line: {line}")
                raise
        return recipe


def load_recipe_dir(path) -> None:
    """Loads all recipe files in a directory"""
    logger.info(f"loading recipe directory: {str(path)!r}")
    for recipe_file in Path(path).iterdir():
        load_recipe_file(recipe_file)


# ------------------------- project -------------------------


def load_project_file(path) -> models.Project:
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
