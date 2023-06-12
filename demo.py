from models import Ingredient, Item, Recipe, db


def view_instance(model):
    print(f"-- {model.__name__} --")
    for instance in model.select():
        print(instance)


db.connect()
db.create_tables([Ingredient, Recipe, Item])


tomate = Ingredient.create(name="tomate")
pan = Ingredient.create(name="pan")

pan_con_tomate = Recipe.create(
    name="pan con tomate",
)

Item.create(ingredient=pan, quantity=1, recipe=pan_con_tomate)
Item.create(ingredient=tomate, quantity=2, recipe=pan_con_tomate)

pan_con_tomate.save()

print("-- Recipes --")
for recipe in Recipe.select():
    print(recipe.description)
    print()
