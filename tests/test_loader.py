import pytest

from planner import loader, models


@pytest.fixture(autouse=True)
def use_database(rollback_transaction):
    """Ensure test database and rollback transaction after each test"""


@pytest.fixture
def pan_con_tomate_recipe():
    return "tests/data/pan con tomate"


@pytest.fixture
def bocata_de_nada_recipe():
    return "tests/data/bocata de nada"


# ------------------------- ingredients -------------------------

# load_ingredients_from_file
# make a ingredient yaml file, and load it
# test atomicity

# ------------------------- recipe -------------------------


def test__Item__create_from_line():
    recipe = models.Recipe.create(name="compote de pommes", serves=1)
    loader.create_item_from_line("2kg pommes", recipe)
    assert len(recipe.items) == 1
    item = recipe.items[0]
    assert item.quantity == 2
    assert item.ingredient.name == "pommes"
    assert item.ingredient.unit == "kg"


def test__Item__create_from_line__conversion():
    recipe = models.Recipe.create(name="compote de pommes", serves=1)
    pommes_item = loader.create_item_from_line("200g pommes", recipe)
    assert str(pommes_item) == "0.2kg pommes"
    wine_item = loader.create_item_from_line("200ml wine", recipe)
    assert str(wine_item) == "0.2l wine"


# ------------------------- parse item line -------------------------


def test__parse_item_line__no_unit():
    assert loader.parse_item_line("1 egg") == ("egg", 1, None)


def test__parse_item_line__case():
    assert loader.parse_item_line("1 EgG") == ("egg", 1, None)


def test__parse_item_line__whitespaces_resistance():
    assert loader.parse_item_line("   1     egg    ") == ("egg", 1, None)


def test__parse_item_line__unit():
    assert loader.parse_item_line("12g ganja") == ("ganja", 12, "g")


def test__parse_item_line__spaces_in_ingredient():
    assert loader.parse_item_line("12g sativa ganja") == (
        "sativa ganja",
        12,
        "g",
    )


def test__parse_item_line__decimal_number():
    assert loader.parse_item_line("1.2g coke") == (
        "coke",
        1.2,
        "g",
    )


def test__parse_item_line__debug():
    assert loader.parse_item_line("4.5kg oats") == (
        "oats",
        4.5,
        "kg",
    )


def test__parse_item_line__unit_and_spaces():
    assert loader.parse_item_line("  12  g    ganja  ") == ("ganja", 12, "g")


def test__parse_item_line__parenthesis():
    assert loader.parse_item_line("12g ganja (well dried)") == (
        "ganja",
        12,
        "g",
    )


def test__parse_item_line__units():
    assert loader.parse_item_line("2kg rice") == ("rice", 2, "kg")


def test__parse_item_line__float():
    assert loader.parse_item_line("2.5kg rice") == ("rice", 2.5, "kg")


def test__parse_item_line__number_zero():
    with raises(Exception):
        loader.parse_item_line("0 apple")


def test__parse_item_line__ingredient_starts_with_l():
    assert loader.parse_item_line("1 lemon") == ("lemon", 1, None)


# ------------------------- load recipe file -------------------------


def test__load_recipe_file(pan_con_tomate_recipe):
    recipe = loader.load_recipe_file(pan_con_tomate_recipe)
    assert recipe.name == "pan con tomate"
    assert recipe.serves == 2
    assert [str(item) for item in recipe.items] == [
        "1.0unit pan",
        "0.1kg tomate rallado",
    ]
    assert (
        recipe.description
        == "pan con tomate (2 persons)\n- 1.0 unit pan\n- 0.1 kg tomate rallado"
    )


def test__load_recipe_file__no_instructions(bocata_de_nada_recipe):
    recipe = loader.load_recipe_file(bocata_de_nada_recipe)
    assert recipe.name == "bocata de nada"
    assert recipe.serves == 1
    assert [str(item) for item in recipe.items] == ["1.0unit pancito", "1.0l aire"]
    assert recipe.instructions is None
