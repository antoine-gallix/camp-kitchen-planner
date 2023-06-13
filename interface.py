from prettytable import PrettyTable

import dialog
from models import Ingredient, Item, Recipe


def choose_or_create_ingredient():
    ingredients = list(Ingredient.select())
    ingredient = dialog.choose(["create ingredient"] + ingredients)
    if ingredient == "create ingredient":
        ingredient = create_ingredient_dialog()
    return ingredient


def view_instances(model):
    table = PrettyTable()
    table.field_names = ["", model.__name__]
    for i, instance in enumerate(model.select()):
        table.add_row((i, instance))
    print(table)


def ingredient_exists(name):
    return Ingredient.get_or_none(Ingredient.name == name) is not None


def create_ingredient_dialog():
    name = input("ingredient name: ")
    if not ingredient_exists(name):
        return Ingredient.create(name=name)
    else:
        print(f"{name!r} already exists")


def create_ingredients():
    continue_ = True
    while continue_:
        print()
        try:
            create_ingredient_dialog()
        except EOFError:
            continue_ = False
        print()


def view_recipes():
    print("-- Recipes --")
    for recipe in models.Recipe.select():
        print(recipe.description)
        print()
