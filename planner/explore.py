from peewee import SQL, fn

import planner


def print_recipes():
    print("-- Recipes --")
    for recipe in planner.models.Recipe.select():
        print()
        print(f"# {recipe.description}")


def count_model(model):
    return model.select(fn.COUNT(SQL("*"))).scalar()


def count_recipes():
    print(f"There are {count_model(planner.models.Recipe)} recipes in the database")


def print_ingredients():
    count = count_model(planner.models.Ingredient)
    print(f"-- Ingredients ({count}) --")
    for ingredient in planner.models.Ingredient.select():
        print(f"{ingredient.name} ({ingredient.unit})")
