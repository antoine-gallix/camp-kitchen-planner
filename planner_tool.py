import click

import planner.loader
import planner.models

main = click.Group()


@main.command()
@click.argument("project")
@click.option("--csv", is_flag=True)
def compute(project, csv):
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
def rescale(recipe, servings):
    planner.models.create_tables()
    recipe = planner.loader.load_recipe_file(recipe)
    rescaled = recipe.rescale(servings)
    print(rescaled.full())
