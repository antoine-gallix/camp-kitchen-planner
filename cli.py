from pathlib import Path

import click
import peewee
from peewee import DatabaseError
from rich import print
from rich.text import Text

from planner import app, config, explore, models, parse
from planner.database import DB
from planner.errors import ParsingError


def print_success(text):
    print(Text(text, style="green"))


def print_error(text):
    print(Text(text, style="red"))


# ------------------------- main -------------------------


main = click.Group()


@main.command("config")
def config_() -> None:
    print(config.as_dict())


@main.command("status")
def db_summary() -> None:
    for model in [models.Project, models.Recipe, models.Ingredient]:
        print(f"{model.__name__} : {explore.count_instances(model)}")


@main.command("UI")
def start_ui() -> None:
    app.MyApp().run()


# ------------------------- database -------------------------


db = click.Group("db")
main.add_command(db)


@db.command("reset")
def reset_db() -> None:
    models.reset_tables()


# ------------------------- tags -------------------------

tags = click.Group("tags")
main.add_command(tags)


@tags.command("list")
def list_tags() -> None:
    explore.print_instances_table(models.Tag)


@tags.command("create")
@click.argument("name", type=click.STRING)
def create_tag(name) -> None:
    tag = models.Tag.create(name=name)
    print_success(f"tag created: {tag!r}")


# ------------------------- ingredient -------------------------

ingredient = click.Group("ingredient")
main.add_command(ingredient)


@ingredient.command("list")
def list_ingredient() -> None:
    explore.print_instances_table(models.Ingredient)


@ingredient.command("show")
@click.argument("id", type=click.INT)
def show_ingredient(id) -> None:
    instance = models.Ingredient.get_by_id(id)
    print(instance.dump())


@ingredient.command("export")
@click.option("--file", type=click.Path(writable=True), default="ingredients.yaml")
def dump_ingredients(file) -> None:
    parse.dump_ingredients(file)


# ------------------------- recipe -------------------------


recipe = click.Group("recipe")
main.add_command(recipe)


@recipe.command("list")
def list_recipe() -> None:
    """List recipes"""
    explore.print_instances_table(models.Recipe)


@recipe.command("load")
@click.argument(
    "file",
    type=click.Path(exists=True, readable=True, resolve_path=True),
)
def load_recipe_into_database(file):
    try:
        if (path := Path(file)).is_file():
            models.Recipe.create_from_file(path)
        else:
            print(f"loading recipes from directory: {path}")
            with DB().atomic():
                for file_path in path.iterdir():
                    models.Recipe.create_from_file(file_path)
    except ParsingError as exc:
        print_error(f"error during parsing. operation canceled: {exc}")
    except DatabaseError as exc:
        print_error(f"error from database during loading. operation canceled: {exc}")


@main.command()
@click.argument("file", type=click.Path(exists=True, readable=True))
def load_recipe_file(file) -> None:
    parse.load_recipe_file(file)


@recipe.command("show")
@click.argument("recipe", type=click.STRING)
@click.option("--rescale", type=click.FLOAT)
def show_recipe(recipe, rescale: int | None = None) -> None:
    """Prin the recipe, with optional rescaling."""
    recipe = models.Recipe.get(name=recipe)
    if rescale:
        recipe = recipe.rescale(rescale)
    print(recipe.full())


@recipe.command("delete")
@click.argument("id", type=click.INT)
def delete_recipe(id) -> None: ...


# ------------------------- project -------------------------

project = click.Group("project")
main.add_command(project)


@project.command("create")
@click.argument("name", type=click.STRING)
@click.argument("servings", type=click.INT)
def create_project(name, servings):
    models.Project.create(name=name, servings=servings)
    print_success("project created")


@project.command("list")
def list_projects() -> None:
    explore.print_instances(models.Project)


@project.command("show")
@click.option("--name", type=click.STRING, default=None)
def show_project(name) -> None:
    if name is not None:
        try:
            project = models.Project.get(name=name)
        except peewee.DoesNotExist:
            print(f"no project named {name}")
            return
    else:
        print("default project")
        project = models.Project.get_default()
    print(project)


@project.command("delete")
@click.argument("name", type=click.STRING)
def delete_project(name) -> None:
    try:
        project = models.Project.get(name=name)
    except peewee.DoesNotExist:
        print_error(f"no project named {name}")
        return
    project.delete_instance()
    print_success(f"project deleted: {project.name}")


@project.command("add")
@click.option(
    "--file",
    type=click.Path(exists=True, dir_okay=False, readable=True, resolve_path=True),
)
@click.option(
    "--name",
    type=click.STRING,
)
@click.option(
    "--id",
    type=click.INT,
)
def add_recipe(file, name, id):
    "add recipe file to default project"
    project = models.Project.get_default()
    if id is not None:
        recipe = models.Recipe.get_by_id(id)
        print(f"recipe fetched from database: {recipe}")
    if name is not None:
        recipe = models.Recipe.get(name=name)
        print(f"recipe fetched from database: {recipe}")
    elif file is not None:
        recipe = models.Recipe.create_from_file(file)
        print(f"recipe created from file: {recipe}")
    models.ProjectItem.create(project=project, recipe=recipe)
    print(f"recipe added to project {project.name!r}: {recipe.name}")


@project.command()
@click.argument("project")
@click.option("--csv", is_flag=True)
def shopping_list(project, csv) -> None:
    project = models.Project.get_default()
    if csv is True:
        project.print_csv_shopping_list()
    else:
        project.print_summary()
        print("--- shopping list ---")
        project.print_shopping_list()


if __name__ == "__main__":
    main()
