from pytest import fixture

from planner import models


@fixture(autouse=True)
def rollback_transaction_here(rollback_transaction):
    ...


def test__Ingredient__save():
    salsifi = models.Ingredient(name="salsifi", type="solid")
    salsifi.save()


def test__Ingredient__repr_str():
    salsifi = models.Ingredient(name="salsifi", type="solid")
    assert repr(salsifi) == "<Ingredient: salsifi>"
    assert str(salsifi) == "salsifi"


def test__Recipe__create():
    pct = models.Recipe(name="pan con tomate", serves=1)
    pct.save()


def test__Recipe__repr_str():
    pan_con_tomate = models.Recipe(name="pan con tomate", serves=1)
    assert repr(pan_con_tomate) == "<Recipe: pan con tomate>"
    assert str(pan_con_tomate) == "pan con tomate"
