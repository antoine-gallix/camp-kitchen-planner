import peewee
from rich import print
from rich.table import Table


def count_instances(model) -> int:
    """Count instances of a model"""
    return model.select(peewee.fn.COUNT(peewee.SQL("*"))).scalar()


def print_instances(model):
    """Print a list of instances"""
    instances = model.select()
    if not instances:
        print(f"no {model.__name__} in the database")
        return
    for instance in instances:
        print(f"- {instance}")


def access_field(instance, accessor):
    match accessor:
        case str(attribute):
            return getattr(instance, attribute)
        case tuple((attribute, function)):
            return function(getattr(instance, attribute))


def field_as_string(field):
    if isinstance(field, list):
        if field:
            return str([str(item) for item in field])
        else:
            return ""
    else:
        return str(field)


def print_instances_table(model):
    """Print a table of instances"""
    instances = model.select()
    if not instances:
        print(f"no {model.__name__} in the database")
        return
    table = Table(title=model.__name__)
    try:
        field_accessor_specs = getattr(model, "_list_fields")
    except AttributeError:
        field_accessor_specs = model._meta.sorted_field_names
    for field_accessor_spec in field_accessor_specs:
        match field_accessor_spec:
            case str(name):
                table.add_column(name)
            case tuple((name, function)):
                table.add_column(f"{function.__name__}({name})")
    for instance in instances:
        instance_fields = (
            access_field(instance, field_accessor_spec)
            for field_accessor_spec in field_accessor_specs
        )

        table.add_row(*tuple(field_as_string(field) for field in instance_fields))
    print(table)
