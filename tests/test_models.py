import peewee
from pytest import fixture, raises

from planner import models


@fixture(autouse=True)
def rollback_transaction_here(rollback_transaction):
    ...


def test__Ingredient__save():
    salsifi = models.Ingredient(name="salsifi", unit="g")
    salsifi.save()


def test__Ingredient__repr_str():
    salsifi = models.Ingredient(name="salsifi", unit="g")
    assert repr(salsifi) == "<Ingredient: salsifi>"
    assert str(salsifi) == "salsifi"


def test__Recipe__create():
    pct = models.Recipe(name="pan con tomate", serves=1)
    pct.save()


def test__Recipe__repr_str():
    pan_con_tomate = models.Recipe(name="pan con tomate", serves=1)
    assert repr(pan_con_tomate) == "<Recipe: pan con tomate>"
    assert str(pan_con_tomate) == "pan con tomate"


def test__Item__create_from_line():
    recipe = models.Recipe.create(name="compote de pommes", serves=1)
    models.Item.create_item_from_line("2kg pommes", recipe)
    assert len(recipe.items) == 1
    item = recipe.items[0]
    assert item.quantity == 2000
    assert item.ingredient.name == "pommes"
    assert item.ingredient.unit == "g"


def test__Ingredient__unique_name_unit__diff_unit():
    models.Ingredient.create(name="pommes", unit="g")
    models.Ingredient.create(name="pommes", unit="unit")


def test__Ingredient__unique_name_unit__all_same():
    models.Ingredient.create(name="pommes", unit="g")
    with raises(peewee.IntegrityError):
        models.Ingredient.create(name="pommes", unit="g")
