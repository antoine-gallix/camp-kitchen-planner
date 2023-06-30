import peewee
from pytest import fixture, raises

from planner import models


@fixture(autouse=True)
def rollback_transaction_here(rollback_transaction):
    ...


@fixture
def pan():
    return models.Ingredient.create(name="pan", unit="unit", price=1.5)


@fixture
def tomate():
    return models.Ingredient.create(name="tomate", unit="kg", price=3)


@fixture
def caracoles():
    return models.Ingredient.create(name="caracoles", unit="kg", price=12)


@fixture
def vinagre():
    return models.Ingredient.create(name="vinagre", unit="l", price=2.5)


@fixture
def pan_con_tomate(pan, tomate):
    recipe = models.Recipe.create(name="pan con tomate", serves=1)
    models.RecipeItem.create(recipe=recipe, ingredient=tomate, quantity=0.1)
    models.RecipeItem.create(recipe=recipe, ingredient=pan, quantity=1)
    return recipe


@fixture
def caracoles_con_vinagre(caracoles, vinagre):
    recipe = models.Recipe.create(name="caracoles con vinagre", serves=1)
    models.RecipeItem.create(recipe=recipe, ingredient=caracoles, quantity=0.05)
    models.RecipeItem.create(recipe=recipe, ingredient=vinagre, quantity=0.25)
    return recipe


@fixture
def feast(pan_con_tomate, caracoles_con_vinagre):
    feast = models.Project.create(name="feast", servings=5)
    models.ProjectItem.create(recipe=pan_con_tomate, project=feast)
    models.ProjectItem.create(recipe=caracoles_con_vinagre, project=feast)
    return feast


# ------------------------- Ingredient -------------------------


def test__Ingredient__save():
    salsifi = models.Ingredient(name="salsifi", unit="kg")
    salsifi.save()


def test__Ingredient__allowed_units():
    # weight
    with raises(ValueError):
        models.Ingredient(name="salsifi", unit="g")
    with raises(ValueError):
        models.Ingredient(name="salsifi", unit="mg")
    models.Ingredient.create(name="salsifi", unit="kg")
    # liquids
    with raises(ValueError):
        models.Ingredient(name="vinagre", unit="ml")
    with raises(ValueError):
        models.Ingredient(name="vinagre", unit="cl")
    with raises(ValueError):
        models.Ingredient(name="vinagre", unit="dl")
    models.Ingredient(name="vinagre", unit="l")
    # spoons and units
    models.Ingredient(name="azucar", unit="tsp")
    models.Ingredient(name="azucal", unit="tbsp")
    models.Ingredient(name="calabaza", unit="unit")
    # anything else
    with raises(ValueError):
        models.Ingredient(name="flores", unit="bund")


def test__Ingredient__price():
    salsifi = models.Ingredient(name="salsifi", unit="kg", price=10)
    salsifi.save()


def test__Ingredient__dump():
    salsifi = models.Ingredient.create(name="salsifi", unit="kg", price=10)
    assert salsifi.dump() == {"name": "salsifi", "price": 10, "unit": "kg"}
    salsifi = models.Ingredient.create(name="tomate", unit="kg")
    assert salsifi.dump() == {"name": "tomate", "unit": "kg"}


def test__Ingredient__lowercase():
    salsifi = models.Ingredient(name="Salsifi", unit="kg")
    salsifi.save()
    assert salsifi.name == "salsifi"


def test__Ingredient__strip():
    salsifi = models.Ingredient(name="   salsifi   ", unit="kg")
    salsifi.save()
    assert salsifi.name == "salsifi"


def test__Ingredient__squash():
    salsifi = models.Ingredient(name="chili  con    carne", unit="kg")
    salsifi.save()
    assert salsifi.name == "chili con carne"


def test__Ingredient__repr_str():
    salsifi = models.Ingredient(name="salsifi", unit="kg")
    assert repr(salsifi) == "<Ingredient(name=salsifi,unit=kg)>"
    assert str(salsifi) == "salsifi"


def test__Ingredient__unique_name_unit__diff_unit():
    models.Ingredient.create(name="pommes", unit="kg")
    models.Ingredient.create(name="pommes", unit="unit")


def test__Ingredient__unique_name_unit__all_same():
    models.Ingredient.create(name="pommes", unit="kg")
    with raises(peewee.IntegrityError):
        models.Ingredient.create(name="pommes", unit="kg")


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


def test__Item__create_from_line():
    recipe = models.Recipe.create(name="compote de pommes", serves=1)
    models.RecipeItem.create_item_from_line("2kg pommes", recipe)
    assert len(recipe.items) == 1
    item = recipe.items[0]
    assert item.quantity == 2
    assert item.ingredient.name == "pommes"
    assert item.ingredient.unit == "kg"


def test__Item__create_from_line__conversion():
    recipe = models.Recipe.create(name="compote de pommes", serves=1)
    pommes_item = models.RecipeItem.create_item_from_line("200g pommes", recipe)
    assert str(pommes_item) == "0.2kg pommes"
    wine_item = models.RecipeItem.create_item_from_line("200ml wine", recipe)
    assert str(wine_item) == "0.2l wine"


def test__parse_item_line__no_unit():
    assert models.RecipeItem.parse_item_line("1 egg") == ("egg", 1, None)


def test__parse_item_line__case():
    assert models.RecipeItem.parse_item_line("1 EgG") == ("egg", 1, None)


def test__parse_item_line__whitespaces_resistance():
    assert models.RecipeItem.parse_item_line("   1     egg    ") == ("egg", 1, None)


def test__parse_item_line__unit():
    assert models.RecipeItem.parse_item_line("12g ganja") == ("ganja", 12, "g")


def test__parse_item_line__spaces_in_ingredient():
    assert models.RecipeItem.parse_item_line("12g sativa ganja") == (
        "sativa ganja",
        12,
        "g",
    )


def test__parse_item_line__decimal_number():
    assert models.RecipeItem.parse_item_line("1.2g coke") == (
        "coke",
        1.2,
        "g",
    )


def test__parse_item_line__debug():
    assert models.RecipeItem.parse_item_line("4.5kg oats") == (
        "oats",
        4.5,
        "kg",
    )


def test__parse_item_line__unit_and_spaces():
    assert models.RecipeItem.parse_item_line("  12  g    ganja  ") == ("ganja", 12, "g")


def test__parse_item_line__parenthesis():
    assert models.RecipeItem.parse_item_line("12g ganja (well dried)") == (
        "ganja",
        12,
        "g",
    )


def test__parse_item_line__units():
    assert models.RecipeItem.parse_item_line("2kg rice") == ("rice", 2, "kg")


def test__parse_item_line__float():
    assert models.RecipeItem.parse_item_line("2.5kg rice") == ("rice", 2.5, "kg")


def test__parse_item_line__number_zero():
    with raises(Exception):
        models.RecipeItem.parse_item_line("0 apple")


def test__parse_item_line__ingredient_starts_with_l():
    assert models.RecipeItem.parse_item_line("1 lemon") == ("lemon", 1, None)


def test__Recipe__str(pan_con_tomate):
    assert str(pan_con_tomate) == "pan con tomate (1 persons)"


def test__Recipe__full__no_instructions(pan_con_tomate):
    assert pan_con_tomate.full() == "serves: 1\n---\n- 0.1kg tomate\n- 1.0unit pan"


def test__Recipe__full__with_instructions(pan_con_tomate):
    pan_con_tomate.instructions = "grate the tomate\nput on top of the bread"
    assert (
        pan_con_tomate.full()
        == "serves: 1\n---\n- 0.1kg tomate\n- 1.0unit pan\n---\ngrate the tomate\nput"
        " on top of the bread"
    )


# ------------------------- Project -------------------------


def test__Project__create_empty():
    models.Project.create(name="feast", servings=5)


def test__Project__repr():
    feast = models.Project.create(name="feast", servings=5)
    assert repr(feast) == "Project(feast for 5 persons)"


def test__Project__create_filled(pan_con_tomate, caracoles_con_vinagre):
    feast = models.Project.create(name="feast", servings=5)
    models.ProjectItem.create(recipe=pan_con_tomate, project=feast)
    models.ProjectItem.create(recipe=caracoles_con_vinagre, project=feast)


def test__Project__shopping_list(feast):
    shopping_list = feast.shopping_list()
    assert [
        f"{quantity}{ingredient.unit} {ingredient.name}"
        for ingredient, quantity in shopping_list.items()
    ] == ["0.5kg tomate", "5.0unit pan", "0.25kg caracoles", "1.25l vinagre"]


def test__Project__priced_shopping_list(feast):
    priced_shopping_list = feast.priced_shopping_list()
    assert [
        f"{quantity}{ingredient.unit} {ingredient.name}: {price} euros"
        for ingredient, quantity, price in priced_shopping_list
    ] == [
        "0.5kg tomate: 1.5 euros",
        "5.0unit pan: 7.5 euros",
        "0.25kg caracoles: 3.0 euros",
        "1.25l vinagre: 3.125 euros",
    ]
