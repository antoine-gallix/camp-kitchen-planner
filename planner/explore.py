from peewee import SQL, fn
from rich import print
from rich.table import Table


def count_instances(model) -> int:
    """Count instances of a model"""
    return model.select(fn.COUNT(SQL("*"))).scalar()


# ------------------------- display -------------------------


def print_instances(model):
    """Print a list of instances"""
    if instances := model.select():
        print(f"-- {model.__name__} [{len(instances)}] --")
        for instance in instances:
            print(f"- {instance}")
    else:
        print(f"no {model.__name__} in the database")


def print_instances_table(model):
    """Print a list of instances"""
    instances = model.select()
    if not instances:
        print(f"no {model.__name__} in the database")
        return
    table = Table(title=model.__name__)
    try:
        fields = getattr(model, "_list_fields")
    except AttributeError:
        fields = model._meta.sorted_field_names
    for field in fields:
        table.add_column(field)
    for instance in instances:
        table.add_row(*tuple(str(getattr(instance, field)) for field in fields))
    print(table)
