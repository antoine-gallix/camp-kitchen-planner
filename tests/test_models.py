from pathlib import Path

import peewee
import pytest
from pytest import fixture, raises

from planner import models
from planner.parse import Quantity, Unit


@fixture(autouse=True)
def rollback_transaction_here(rollback_transaction): ...


# --- tags


@fixture
def fresh():
    return models.Tag.create(name="fresh")


@fixture
def delicious():
    return models.Tag.create(name="delicious")


@fixture
def uncommon():
    return models.Tag.create(name="uncommon")


# --- ingredients


@fixture
def pan():
    return models.Ingredient.create(name="pan", unit=Unit.UNIT, price=1.5)


@fixture
def tomate():
    return models.Ingredient.create(name="tomate", unit=Unit.KILOGRAM, price=3)


@fixture
def caracoles():
    return models.Ingredient.create(name="caracoles", unit=Unit.KILOGRAM, price=12)


@fixture
def vinagre():
    return models.Ingredient.create(name="vinagre", unit=Unit.LITER, price=2.5)


# --- recipes


@fixture
def pan_con_tomate(pan, tomate):
    recipe = models.Recipe.create(name="pan con tomate", serves=1)
    models.RecipeItem.create(recipe=recipe, ingredient=tomate, quantity=0.1)
    models.RecipeItem.create(recipe=recipe, ingredient=pan, quantity=1)
    return recipe


@fixture
def caracoles_con_vinagre(caracoles, vinagre):
    recipe = models.Recipe.create(name="caracoles con vinagre", serves=1)
    models.RecipeItem.create(recipe=recipe, ingredient=caracoles, quantity=50)
    models.RecipeItem.create(recipe=recipe, ingredient=vinagre, quantity=0.25)
    return recipe


# --- project


@fixture
def feast(pan_con_tomate, caracoles_con_vinagre):
    feast = models.Project.create(name="feast")
    models.ProjectRecipe.create(recipe=pan_con_tomate, project=feast, servings=5)
    models.ProjectRecipe.create(recipe=caracoles_con_vinagre, project=feast, servings=5)
    return feast


# ------------------------- tag -------------------------


def test__Tag__save():
    fresh = models.Tag(name="fresh")
    fresh.save()


def test__Tag__unique():
    models.Tag.create(name="fresh")
    with raises(peewee.IntegrityError):
        models.Tag.create(name="fresh")


def test__Tag__repr(fresh):
    assert repr(fresh) == "<Tag('fresh')>"


def test__Tag__str(fresh):
    assert str(fresh) == "fresh"


# ------------------------- Ingredient -------------------------


def test__Ingredient__save():
    salsifi = models.Ingredient(name="salsifi", unit=Unit.KILOGRAM)
    salsifi.save()


def test__Ingredient__allowed_units():
    # weight
    with raises(ValueError):
        models.Ingredient(name="salsifi", unit="g")
    with raises(ValueError):
        models.Ingredient(name="salsifi", unit="mg")
    models.Ingredient.create(name="salsifi", unit=Unit.KILOGRAM)
    # liquids
    with raises(ValueError):
        models.Ingredient(name="vinagre", unit="ml")
    with raises(ValueError):
        models.Ingredient(name="vinagre", unit="cl")
    with raises(ValueError):
        models.Ingredient(name="vinagre", unit="dl")
    models.Ingredient(name="vinagre", unit=Unit.LITER)
    # spoons and units
    models.Ingredient(name="azucar", unit=Unit.TEASPOON)
    models.Ingredient(name="azucal", unit=Unit.TABLESPOON)
    models.Ingredient(name="calabaza", unit=Unit.UNIT)
    # anything else
    with raises(ValueError):
        models.Ingredient(name="flores", unit="bund")


def test__Ingredient__price():
    salsifi = models.Ingredient(name="salsifi", unit=Unit.KILOGRAM, price=10)
    salsifi.save()


def test__Ingredient__dump():
    salsifi = models.Ingredient.create(name="salsifi", unit=Unit.KILOGRAM, price=10)
    assert salsifi.dump() == {
        "name": "salsifi",
        "price": 10,
        "unit": "kilogram",
        "tags": [],
    }
    salsifi = models.Ingredient.create(name="tomate", unit=Unit.KILOGRAM)
    assert salsifi.dump() == {"name": "tomate", "unit": "kilogram", "tags": []}


def test__Ingredient__lowercase():
    salsifi = models.Ingredient(name="Salsifi", unit=Unit.KILOGRAM)
    salsifi.save()
    assert salsifi.name == "salsifi"


def test__Ingredient__strip():
    salsifi = models.Ingredient(name="   salsifi   ", unit=Unit.KILOGRAM)
    salsifi.save()
    assert salsifi.name == "salsifi"


def test__Ingredient__squash():
    salsifi = models.Ingredient(name="chili  con    carne", unit=Unit.KILOGRAM)
    salsifi.save()
    assert salsifi.name == "chili con carne"


def test__Ingredient__repr_str():
    salsifi = models.Ingredient(name="salsifi", unit=Unit.KILOGRAM)
    assert repr(salsifi) == "<Ingredient(name=salsifi,unit=kilogram)>"
    assert str(salsifi) == "salsifi"


def test__Ingredient__unique_name_unit__diff_unit():
    models.Ingredient.create(name="pommes", unit=Unit.KILOGRAM)
    models.Ingredient.create(name="pommes", unit=Unit.UNIT)


def test__Ingredient__unique_name_unit__all_same():
    models.Ingredient.create(name="pommes", unit=Unit.KILOGRAM)
    with raises(peewee.IntegrityError):
        models.Ingredient.create(name="pommes", unit=Unit.KILOGRAM)


def test__Ingredient__add_tag(tomate, fresh):
    tomate.add_tag(fresh)
    assert tomate.tags == [fresh]


def test__Tag__add_to_tag_only_once(tomate, fresh):
    tomate.add_tag(fresh)
    tomate.add_tag(fresh)
    assert [tag.name for tag in tomate.tags] == ["fresh"]


def test__Tag__multiple_tag_to_ingredient(tomate, fresh, delicious):
    tomate.add_tag(fresh)
    tomate.add_tag(delicious)
    assert list(tomate.tags) == [fresh, delicious]


def test__Tag__to_multiple_ingredients(tomate, caracoles, fresh):
    tomate.add_tag(fresh)
    caracoles.add_tag(fresh)
    assert list(tomate.tags) == [fresh]
    assert list(caracoles.tags) == [fresh]


def test__Ingredient__category_usual(tomate):
    assert tomate.category == "usual"


def test__Ingredient__category_fresh(tomate, fresh):
    tomate.add_tag(fresh)
    assert tomate.category == "fresh"


def test__Ingredient__category_uncommon(tomate, fresh, uncommon):
    tomate.add_tag(fresh)
    tomate.add_tag(uncommon)
    assert tomate.category == "uncommon"


# ------------------------- Recipe -------------------------


# --- creation
def test__Recipe__create():
    pct = models.Recipe.create(name="pan con tomate", serves=1)


def test__Recipe__all_required():
    with raises(peewee.IntegrityError):
        models.Recipe.create(name="pan con tomate")
    with raises(peewee.IntegrityError):
        models.Recipe.create(serves=1000)


def test__Recipe__lowercase():
    pct = models.Recipe(name="Pan Con Tomate", serves=1)
    pct.save()
    assert pct.name == "pan con tomate"


def test__Recipe__strip():
    pct = models.Recipe(name="   pan con tomate   ", serves=1)
    pct.save()
    assert pct.name == "pan con tomate"


def test__Recipe__squash():
    salsifi = models.Recipe(name="chili  con    carne", serves=12)
    salsifi.save()
    assert salsifi.name == "chili con carne"


def test__Recipe__repr():
    pan_con_tomate = models.Recipe(name="pan con tomate", serves=1)
    assert repr(pan_con_tomate) == "<Recipe: pan con tomate (1 persons)>"


def test__Recipe__str():
    pan_con_tomate = models.Recipe(name="pan con tomate", serves=1)
    assert str(pan_con_tomate) == "pan con tomate (1 persons)"


# --- build


def test__Recipe__build():
    recipe = models.Recipe.create(name="pan con tomate", serves=1)
    recipe.add_item(Quantity.from_tuple(100, "g"), "tomate")
    recipe.add_item(Quantity.from_tuple(1, "unit"), "pan")
    assert [
        (item.quantity, str(item.ingredient.unit), item.ingredient.name)
        for item in recipe.items
    ] == [(0.1, "kilogram", "tomate"), (1.0, "unit", "pan")]


# --- creation


def test__Recipe__full__no_instructions(pan_con_tomate):
    assert pan_con_tomate.as_text().split("\n") == [
        "serves: 1",
        "---",
        "- 0.100 kilogram tomate",
        "- 1.000 unit pan",
    ]


def test__Recipe__full__with_instructions(pan_con_tomate):
    pan_con_tomate.instructions = "grate the tomate\nput on top of the bread"
    assert pan_con_tomate.as_text().split("\n") == [
        "serves: 1",
        "---",
        "- 0.100 kilogram tomate",
        "- 1.000 unit pan",
        "---",
        "grate the tomate",
        "put on top of the bread",
    ]


# from file

TEST_DATA = Path("tests/data")
PAN_CON_TOMATE_RECIPE_FILE = TEST_DATA / "pan con tomate"
BOCATA_DE_NADA_RECIPE = TEST_DATA / "bocata de nada"


def test__Recipe__from_file():
    recipe = models.Recipe.create_from_file(PAN_CON_TOMATE_RECIPE_FILE)
    assert recipe.name == "pan con tomate"
    assert recipe.serves == 2


# ------------------------- Project -------------------------


def test__Project__create_empty():
    models.Project.create(name="feast")


def test__Project__repr(feast):
    assert repr(feast) == "Project(name=feast)"


def test__Project__str(feast):
    assert str(feast) == "feast: 2 recipes"


def test__Project__create_filled(pan_con_tomate, caracoles_con_vinagre):
    feast = models.Project.create(name="feast")
    models.ProjectRecipe.create(recipe=pan_con_tomate, project=feast, servings=5)
    models.ProjectRecipe.create(recipe=caracoles_con_vinagre, project=feast, servings=5)
    assert [(item.recipe.name, item.servings) for item in feast.items] == [
        ("pan con tomate", 5),
        ("caracoles con vinagre", 5),
    ]


def test__Project__add_recipe(pan_con_tomate, caracoles_con_vinagre):
    feast = models.Project.create(name="feast")
    feast.add_recipe(recipe=pan_con_tomate, servings=5)
    feast.add_recipe(recipe=caracoles_con_vinagre, servings=5)
    assert [(item.recipe.name, item.servings) for item in feast.items] == [
        ("pan con tomate", 5),
        ("caracoles con vinagre", 5),
    ]


def test__Project__shopping_list(feast, pan, tomate, caracoles, vinagre):
    shopping_list = feast.shopping_list()
    assert shopping_list == [
        (tomate, 0.5),
        (pan, 5),
        (caracoles, 250),
        (vinagre, 1.25),
    ]


def test__Project__priced_shopping_list(feast, pan, tomate, caracoles, vinagre):
    priced_shopping_list = feast.priced_shopping_list()
    assert priced_shopping_list == [
        (tomate, 0.5, 1.5),
        (pan, 5, 7.5),
        (caracoles, 250, 3000),
        (vinagre, 1.25, 3.125),
    ]
