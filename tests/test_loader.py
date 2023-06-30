import pytest

import planner.loader


@pytest.fixture(autouse=True)
def rollback_transaction_here(rollback_transaction):
    ...


@pytest.fixture
def pan_con_tomate_recipe():
    return "tests/pan con tomate"


@pytest.fixture
def bocata_de_nada_recipe():
    return "tests/bocata de nada"


def test__load_recipe_file(pan_con_tomate_recipe):
    recipe = planner.loader.load_recipe_file(pan_con_tomate_recipe)
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
    recipe = planner.loader.load_recipe_file(bocata_de_nada_recipe)
    assert recipe.name == "bocata de nada"
    assert recipe.serves == 1
    assert [str(item) for item in recipe.items] == ["1.0unit pancito", "1.0l aire"]
    assert recipe.instructions is None
