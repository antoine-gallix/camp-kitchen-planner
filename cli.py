from pathlib import Path

import click
import funcy
import peewee
import yaml
from peewee import DatabaseError
from rich import print, rule
from rich.text import Text
from yaml import Loader, load_all

from planner import app, config, explore, models
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
    for model in [models.Project, models.Recipe, models.Ingredient, models.Tag]:
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


@tags.command("delete")
@click.argument("id", type=click.INT)
def delete_tag(id) -> None:
    tag = models.Tag.get_by_id(id)
    tag.delete_instance()
    print_success(f"tag removed: {tag!r}")


@tags.command("update-from-file")
@click.argument("file", type=click.Path(exists=True, readable=True))
@click.option("--create-tags", is_flag=True)
def update_tags_from_file(file, create_tags) -> None:
    ingredient_update = list(load_all(Path(file).open(), Loader=Loader))
    tag_names = set(
        funcy.flatten(ingredient["tags"] for ingredient in ingredient_update)
    )
    if create_tags:
        tags = {}
        for tag_name in tag_names:
            tag, created = models.Tag.get_or_create(name=tag_name)
            if created:
                print_success(f"tag created: {tag!r}")
            tags[tag_name] = tag
    else:
        tags = {tag_name: models.Tag.get(name=tag_name) for tag_name in tag_names}
    for update_item in ingredient_update:
        try:
            ingredient = models.Ingredient.get(name=update_item["name"])
            for tag in (tags[tag_name] for tag_name in update_item["tags"]):
                ingredient.add_tag(tag)
        except peewee.DoesNotExist:
            print_error(f"could not find ingredient: {update_item["name"]}")


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
@click.argument("file", type=click.Path(writable=True))
def dump_ingredients(file) -> None:
    print(f"writing ingredients in {file!r}")
    serialized = [ingredient.dump() for ingredient in models.Ingredient.select()]
    yaml.dump_all(serialized, Path(file).open("w"))


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


@recipe.command("show")
@click.option("--name", type=click.STRING)
@click.option("--id", type=click.INT)
@click.option("--rescale", type=click.FLOAT)
def show_recipe(name, id, rescale: int | None = None) -> None:
    """Prin the recipe, with optional rescaling."""
    if id is not None:
        recipe = models.Recipe.get_by_id(id)
    elif name is not None:
        recipe = models.Recipe.get(name=recipe)
    else:
        print_error("recipe not found")
    if rescale:
        recipe = recipe.rescale(rescale)
    print(rule.Rule(recipe.name))
    print(recipe.full())


@recipe.command("delete")
@click.argument("id", type=click.INT)
def delete_recipe(id) -> None: ...


# ------------------------- project -------------------------

project = click.Group("project")
main.add_command(project)


def select_project(name):
    if name is not None:
        try:
            return models.Project.get(name=name)
        except peewee.DoesNotExist:
            raise ValueError(f"no project named {name}")
    else:
        print("using default project")
        return models.Project.get_default()


@project.command("create")
@click.argument("name", type=click.STRING)
def create_project(name):
    models.Project.create(name=name)
    print_success("project created")


@project.command("list")
def list_projects() -> None:
    explore.print_instances(models.Project)


@project.command("show")
@click.option("--name", type=click.STRING, default=None)
def show_project(name) -> None:
    project = select_project(name)
    print(project.detail_printable())


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
@click.option("--servings", type=click.INT)
@click.option("--project", type=click.STRING)
def add_recipe(file, name, id, servings, project):
    "Add recipe file to default project"
    # project
    project = select_project(project)
    # recipe
    if id is not None:
        recipe = models.Recipe.get_by_id(id)
        print(f"recipe fetched from database: {recipe}")
    elif name is not None:
        recipe = models.Recipe.get(name=name)
        print(f"recipe fetched from database: {recipe}")
    elif file is not None:
        recipe = models.Recipe.create_from_file(file)
        print(f"recipe created from file: {recipe}")
    else:
        print_error("could not find recipe")
    if not servings:
        print("no rescaling")
        servings = recipe.serves
    project.add_recipe(recipe=recipe, servings=servings)
    print(f"recipe added to project {project.name!r}: {recipe.name!r} for {servings}")


@project.command()
@click.option("--csv", is_flag=True)
@click.option("--name", type=click.STRING)
def shopping_list(csv, name) -> None:
    project = select_project(name)
    if csv is True:
        project.print_csv_shopping_list()
    else:
        print(project.detail_printable())
        print(project.shopping_list_table())


if __name__ == "__main__":
    main()
