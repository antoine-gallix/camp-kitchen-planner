from peewee import SQL, fn
import planner


def count_model(model) -> int:
    """Count instances of a model"""
    return model.select(fn.COUNT(SQL("*"))).scalar()


# ------------------------- display -------------------------


def print_instances(model):
    """Print a list of instances"""
    if instances := model.select().get_or_none():
        print(f"-- {model.__name__} --")
        for instance in instances:
            print(instance)
    else:
        print(f"no instances of {model.__name__} in database")


def count_recipes():
    """Print model instance count"""
    print(f"There are {count_model(planner.models.Recipe)} recipes in the database")
