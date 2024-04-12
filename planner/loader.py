import re
from dataclasses import dataclass
from pathlib import Path


import funcy
import yaml
from typing import Any
from planner import logger, models


# ------------------------- ingredients -------------------------


def load_ingredients_from_file(file_path) -> None:
    logger.info(f"loading ingredients from file {file_path}")
    ingredient_data = list(yaml.load_all(Path(file_path).open(), Loader=yaml.Loader))
    logger.info(f"file contains {len(ingredient_data)} ingredients")
    for d in ingredient_data:
        models.Ingredient.create(**d)


# ------------------------- recipe -------------------------


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
