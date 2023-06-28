import click

import planner.loader
import planner.models


@click.command()
@click.argument("project")
def plan(project):
    planner.models.create_tables()
    planner.loader.load_ingredients_from_file("ingredients.yaml")
    planner.loader.load_recipe_dir("recipes")
    project = planner.loader.load_project_file(project)
    project.print_summary()
    print("--- shopping list ---")
    project.print_shopping_list()
