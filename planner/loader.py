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
    logger.debug(f"loading recipe {str(path)!r}")
    header, items = parse_recipe_file(path)
    recipe = models.Recipe.create(**header)
    for line in items:
        try:
            item = models.RecipeItem.create_item_from_line(line, recipe)
        except:
            logger.debug(f"could not parse item line: {line}")
            raise


def load_recipe_dir(path):
    logger.info(f"loading recipe directory: {str(path)!r}")
    for recipe_file in Path(path).iterdir():
        load_recipe_file(recipe_file)


def load_project_file(path):
    file_ = Path(path)
    project_data = yaml.load(file_.read_text(), yaml.Loader)
    project = models.Project.create(name=file_.stem, servings=project_data["servings"])
    for recipe_name in project_data["recipes"]:
        recipe = models.Recipe.get(name=recipe_name)
        models.ProjectItem.create(project=project, recipe=recipe)
    return project
