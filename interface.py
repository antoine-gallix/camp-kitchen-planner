from prettytable import PrettyTable

from models import Ingredient, Item, Recipe


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
        Ingredient.create(name=name)
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
