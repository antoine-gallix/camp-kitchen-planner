from peewee import SQL, fn

import planner


def view_recipes():
    print("-- Recipes --")
    for recipe in planner.models.Recipe.select():
        print()
        print(f"# {recipe.description}")


def count_recipes():
    count = planner.models.Recipe.select(fn.COUNT(SQL("*"))).scalar()
    print(f"There are {count} recipes in the database")
