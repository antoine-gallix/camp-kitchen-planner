from collections import defaultdict
from pathlib import Path

from yaml import dump

from planner import logger, models, parse


def make_shopping_list(project_file):
    project = parse.load_yaml_file(project_file)

    shoppinglist = defaultdict(int)
    for dish in project:
        recipe = models.Recipe.get(models.Recipe.name == dish["recipe"])
        for item in recipe.items:
            shoppinglist[item.ingredient.name] += (
                item.quantity * dish["servings"] / recipe.serves
            )
    return shoppinglist


def export_ingredient_base():
    base_dir = Path("base")
    base_dir.mkdir(exist_ok=True)

    tags = [tag.name for tag in models.Tag]
    tag_file = base_dir / "tags"
    logger.info(f"exporting {len(tags)} tags to {tag_file}")
    tag_file.write_text(dump(tags))

    ingredients = [ingredient.dump() for ingredient in models.Ingredient]
    ingredient_file = base_dir / "ingredients"
    logger.info(f"exporting {len(ingredients)} ingredients to {ingredient_file}")
    ingredient_file.write_text(dump(ingredients))
