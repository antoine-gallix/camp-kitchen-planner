import click

from planner import loader
from planner import explore
from planner import models
from planner import app

main = click.Group()


@main.command()
@click.argument("project")
@click.option("--csv", is_flag=True)
def compute(project, csv) -> None:
    models.create_tables()
    loader.load_ingredients_from_file("ingredients.yaml")
    loader.load_recipe_dir("recipes")
    project = loader.load_project_file(project)
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
    models.create_tables()
    recipe = loader.load_recipe_file(recipe)
    rescaled = recipe.rescale(servings)
    print(rescaled.full())


@main.command()
def dump_ingredient_from_recipes() -> None:
    models.create_tables()
    loader.load_recipe_dir("recipes/")
    loader.dump_ingredients("ingredients.yaml")


@main.command()
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
    models.reset_tables()


@main.command()
def db_summary() -> None:
    for model in [models.Project, models.Recipe, models.Ingredient]:
        print(f"{model.__name__} : {explore.count_instances(model)}")


@main.command()
def run() -> None:
    app.MyApp().run()
