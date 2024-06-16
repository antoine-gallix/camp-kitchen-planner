from collections import defaultdict

import dialog
from prettytable import PrettyTable

from planner import models, parse


def view_instances(model):
    table = PrettyTable()
    table.field_names = ["", model.__name__]
    for i, instance in enumerate(model.select()):
        table.add_row((i, instance))
    print(table)


# ------------------------- ingredients -------------------------


def get_ingredient_by_name(name):
    return models.Ingredient.get_or_none(models.Ingredient.name == name)


def ingredient_exists(name):
    return get_ingredient_by_name is not None


def create_ingredient_dialog():
    name = input("ingredient name: ")
    if not ingredient_exists(name):
        return models.Ingredient.create(name=name)
    else:
        print(f"{name!r} already exists")


def choose_or_create_ingredient():
    ingredients = list(models.Ingredient.select())
    ingredient = dialog.choose(["create ingredient"] + ingredients)
    if ingredient == "create ingredient":
        ingredient = create_ingredient_dialog()
    return ingredient


def create_ingredients():
    continue_ = True
    while continue_:
        print()
        try:
            create_ingredient_dialog()
        except EOFError:
            continue_ = False
        print()


def view_ingredients():
    view_instances(models.Ingredient)


# ------------------------- recipes -------------------------


def view_recipes():
    print("-- Recipes --")
    for recipe in models.Recipe.select():
        print(recipe.description)
        print()


def create_recipe():
    print("recipe creation")
    recipe = None
    while recipe is None:
        recipe_name = input("name: ")
        if recipe_exists(recipe_name):
            print("recipe with this name already exists")
        else:
            recipe = models.Recipe.create(name=recipe_name)

    continue_ = True
    while continue_:
        try:
            print("choose an ingredient")
            ingredient = choose_or_create_ingredient()
            quantity = input("which quantity?: ")
            models.IngredientQuantity.create(
                recipe=recipe, ingredient=ingredient, quantity=quantity
            )
        except EOFError:
            continue_ = False
    print("recipe created")
    print(recipe.description)
