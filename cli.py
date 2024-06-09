import click
import peewee
from rich import print

from planner import app, config, db, explore, loader, models

main = click.Group()


@main.command("config")
def config_() -> None:
    print(config.as_dict())


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
@click.argument("file", type=click.Path(exists=True, readable=True))
def load_recipe_file(file) -> None:
    loader.load_recipe_file(file)




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


@main.command("UI")
def start_ui() -> None:
    app.MyApp().run()


# ------------------------- recipe -------------------------



# ------------------------- project -------------------------

@main.command()
@click.argument("name",type=click.STRING)
@click.argument("servings",type=click.INT)
def create_project(name,servings):
    models.Project.create(name=name,servings=servings)

@main.command()
def list_projects() -> None:
    explore.print_instances(models.Project)

@main.command()
@click.argument("name",type=click.STRING)
def delete_project(name) -> None:
    try:
        project=models.Project.get(name=name)
    except peewee.DoesNotExist:
        print(f"no project named {name}")
        return
    project.delete_instance()
    print(f"project deleted: {project.name}")



if __name__ == "__main__":
    main()
