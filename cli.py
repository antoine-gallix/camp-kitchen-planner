import click
import peewee
from rich import print
from rich.text import Text

from planner import app, config, db, explore, loader, models


def print_success(text):
    print(Text(text,style="green"))

def print_error(text):
    print(Text(text,style="red"))


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


recipe = click.Group('recipe')
main.add_command(recipe)

@recipe.command("parse")
@click.argument("file",type=click.Path(exists=True,dir_okay=False,readable=True,resolve_path=True))
def parse_recipe(file):
    recipe=models.Recipe.from_file(file)
    print(recipe)

@recipe.command("add")
@click.argument("file",type=click.Path(exists=True,dir_okay=False,readable=True,resolve_path=True))
def add_recipe(file):
    project = models.Project.get_default()
    print(f"adding recipe to project {project.name}: {file}")
    recipe=models.Recipe.from_file(file)
    print(recipe)

@recipe.command("delete")
@click.argument("id",type=click.INT)
def delete_recipe(id) -> None:
    ...



# ------------------------- project -------------------------

project = click.Group('project')
main.add_command(project)

@project.command("create")
@click.argument("name",type=click.STRING)
@click.argument("servings",type=click.INT)
def create_project(name,servings):
    models.Project.create(name=name,servings=servings)
    print_success("project created")

@project.command("list")
def list_projects() -> None:
    explore.print_instances(models.Project)


@project.command("show")
@click.option("--name",type=click.STRING,default=None)
def show_project(name) -> None:
    if name is not None:
        try:
            project=models.Project.get(name=name)
        except peewee.DoesNotExist:
            print(f"no project named {name}")
            return
    else:
        print('default project')
        project=models.Project.get_default()
    print(project)

@project.command("delete")
@click.argument("name",type=click.STRING)
def delete_project(name) -> None:
    try:
        project=models.Project.get(name=name)
    except peewee.DoesNotExist:
        print_error(f"no project named {name}")
        return
    project.delete_instance()
    print_success(f"project deleted: {project.name}")




if __name__ == "__main__":
    main()
