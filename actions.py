from collections import defaultdict

from planner import parse
from planner import models


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
