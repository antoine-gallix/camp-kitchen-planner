import peewee
from peewee import SQL, fn

import planner


def count_instances(model) -> int:
    """Count instances of a model"""
    return model.select(fn.COUNT(SQL("*"))).scalar()


# ------------------------- display -------------------------


def print_instances(model):
    """Print a list of instances"""
    if instances:= model.select():
        print(f"-- {model.__name__} [{len(instances)}] --")
        for instance in instances:
            print(f"- {instance}")
    else:
        print(f"no {model.__name__} in the database")
