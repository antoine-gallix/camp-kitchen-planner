import peewee
from pytest import fixture, raises

from planner import models
from planner.parse import Unit


@fixture(autouse=True)
def rollback_transaction_here(rollback_transaction): ...


# --- tags


@fixture
def fresh():
    return models.Tag.create(name="fresh")


@fixture
def delicious():
    return models.Tag.create(name="delicious")


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
    feast = models.Project.create(name="feast", servings=5)
    models.ProjectItem.create(recipe=pan_con_tomate, project=feast)
    models.ProjectItem.create(recipe=caracoles_con_vinagre, project=feast)
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
    assert salsifi.dump() == {"name": "salsifi", "price": 10, "unit": "kilogram"}
    salsifi = models.Ingredient.create(name="tomate", unit=Unit.KILOGRAM)
    assert salsifi.dump() == {"name": "tomate", "unit": "kilogram"}


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
    assert list(tomate.tags) == [fresh]


def test__Tag__add_to_tag_only_once(tomate, fresh):
    tomate.add_tag(fresh)
    with raises(peewee.IntegrityError):
        tomate.add_tag(fresh)


def test__Tag__multiple_tag_to_ingredient(tomate, fresh, delicious):
    tomate.add_tag(fresh)
    tomate.add_tag(delicious)
    assert list(tomate.tags) == [fresh, delicious]


def test__Tag__to_multiple_ingredients(tomate, caracoles, fresh):
    tomate.add_tag(fresh)
    caracoles.add_tag(fresh)
    assert list(tomate.tags) == [fresh]
    assert list(caracoles.tags) == [fresh]


# ------------------------- Recipe -------------------------


def test__Recipe__create():
    pct = models.Recipe(name="pan con tomate", serves=1)
    pct.save()


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


def test__Recipe__full__no_instructions(pan_con_tomate):
    assert pan_con_tomate.full().split("\n") == [
        "serves: 1",
        "---",
        "- 0.1 kilogram tomate",
        "- 1.0 unit pan",
    ]


def test__Recipe__full__with_instructions(pan_con_tomate):
    pan_con_tomate.instructions = "grate the tomate\nput on top of the bread"
    assert pan_con_tomate.full().split("\n") == [
        "serves: 1",
        "---",
        "- 0.1 kilogram tomate",
        "- 1.0 unit pan",
        "---",
        "grate the tomate",
        "put on top of the bread",
    ]


def test__Recipe__full__rescale(pan_con_tomate):
    rescaled = pan_con_tomate.rescale(5)
    assert rescaled.name == "pan con tomate rescaled for 5"
    assert rescaled.serves == 5
    assert [str(item) for item in rescaled.items] == [
        "0.5 kilogram tomate",
        "5.0 unit pan",
    ]


# from file

PAN_CON_TOMATE_RECIPE_FILE = "tests/data/pan con tomate"
BOCATA_DE_NADA_RECIPE = "tests/data/bocata de nada"


def test__Recipe__from_file():
    recipe = models.Recipe.create_from_file(PAN_CON_TOMATE_RECIPE_FILE)
    assert recipe.name == "pan con tomate"
    assert recipe.serves == 2


# ------------------------- Project -------------------------


def test__Project__create_empty():
    models.Project.create(name="feast", servings=5)


def test__Project__repr(feast):
    assert repr(feast) == "Project(name=feast,servings=5)"


def test__Project__str(feast):
    assert str(feast) == "feast: 2 recipes for 5 servings"


def test__Project__create_filled(pan_con_tomate, caracoles_con_vinagre):
    feast = models.Project.create(name="feast", servings=5)
    models.ProjectItem.create(recipe=pan_con_tomate, project=feast)
    models.ProjectItem.create(recipe=caracoles_con_vinagre, project=feast)


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


# ------------------------- recipe -------------------------


# def test__Item__create_from_line():
#     recipe = models.Recipe.create(name="compote de pommes", serves=1)
#     parse.create_item_from_line("2kg pommes", recipe)
#     assert len(recipe.items) == 1
#     item = recipe.items[0]
#     assert item.quantity == 2
#     assert item.ingredient.name == "pommes"
#     assert item.ingredient.unit == "kg"


# def test__Item__create_from_line__conversion():
#     recipe = models.Recipe.create(name="compote de pommes", serves=1)
#     pommes_item = parse.create_item_from_line("200g pommes", recipe)
#     assert str(pommes_item) == "0.2kg pommes"
#     wine_item = parse.create_item_from_line("200ml wine", recipe)
#     assert str(wine_item) == "0.2l wine"


# ------------------------- ingredients -------------------------

# load_ingredients_from_file
# make a ingredient yaml file, and load it
# test atomicity
