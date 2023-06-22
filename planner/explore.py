import planner


def view_recipes():
    print("-- Recipes --")
    for recipe in planner.models.Recipe.select():
        print()
        print(f"# {recipe.description}")
