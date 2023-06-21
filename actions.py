from collections import defaultdict

import loader
import models


def make_shopping_list(project_file):
    project = loader.load_yaml_file(project_file)

    shoppinglist = defaultdict(int)
    for dish in project:
        recipe = models.Recipe.get(models.Recipe.name == dish["recipe"])
        for item in recipe.items:
            shoppinglist[item.ingredient.name] += (
                item.quantity * dish["servings"] / recipe.serves
            )
    return shoppinglist
