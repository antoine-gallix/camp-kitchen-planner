import click

import planner.loader
import planner.models

main = click.Group()


@main.command()
@click.argument("project")
@click.option("--csv", is_flag=True)
def compute(project, csv) -> None:
    planner.models.create_tables()
    planner.loader.load_ingredients_from_file("ingredients.yaml")
    planner.loader.load_recipe_dir("recipes")
    project = planner.loader.load_project_file(project)
    if csv is True:
        project.print_csv_shopping_list()
    else:
        project.print_summary()
        print("--- shopping list ---")
        project.print_shopping_list()


@main.command()
@click.argument("recipe")
@click.argument("servings", type=click.FLOAT)
def rescale(recipe, servings) -> None:
    planner.models.create_tables()
    recipe = planner.loader.load_recipe_file(recipe)
    rescaled = recipe.rescale(servings)
    print(rescaled.full())


@main.command()
def recipe() -> None:
    if recipes := planner.models.Recipe.select().get_or_none():
        for recipe in recipes:
            print(recipe)
    else:
        print("no recipes")
def list_recipe() -> None:
    explore.print_instances(models.Project)


@main.command()
def list_project() -> None:
    explore.print_instances(models.Recipe)


@main.command()
def list_ingredient() -> None:
    explore.print_instances(models.Ingredient)


@main.command()
def reset_db() -> None:
    planner.models.reset_tables()

@main.command()
def db_summary() -> None:
    for model in [models.Project, models.Recipe, models.Ingredient]:
        print(f"{model.__name__} : {explore.count_instances(model)}")
