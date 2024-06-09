import pytest

from planner.errors import ParsingError
from planner.parse import (
    Quantity,
    Unit,
    _parse_item_line,
    _split_recipe_file,
    parse_recipe_file,
)

# ------------------------- quantity -------------------------

def test_quantity__error():
    with pytest.raises(ParsingError):
        assert Quantity.from_tuple(1,"plic")


def test_quantity__basic_units():
    assert Quantity.from_tuple(1,"g")==Quantity(1,Unit.GRAM)
    assert Quantity.from_tuple(1,"l")==Quantity(1,Unit.LITER)
    assert Quantity.from_tuple(1,"u")==Quantity(1,Unit.UNIT)
    assert Quantity.from_tuple(1,"tsp")==Quantity(1,Unit.TEASPOON)
    assert Quantity.from_tuple(1,"tbsp")==Quantity(1,Unit.TABLESPOON)

def test_quantity__conversions():
    assert Quantity.from_tuple(1000,"mg")==Quantity(1,Unit.GRAM)
    assert Quantity.from_tuple(1,"kg")==Quantity(1000,Unit.GRAM)
    
    assert Quantity.from_tuple(1000,"ml")==Quantity(1,Unit.LITER)
    assert Quantity.from_tuple(100,"cl")==Quantity(1,Unit.LITER)
    assert Quantity.from_tuple(10,"dl")==Quantity(1,Unit.LITER)



# ------------------------- parse item line -------------------------


def test__parse_item_line__no_unit():
    assert _parse_item_line("1 egg") == (Quantity(1.0,Unit.UNIT), 'egg')


def test__parse_item_line__case():
    assert _parse_item_line("1 EgG") ==(Quantity(1.0,Unit.UNIT), 'egg')


def test__parse_item_line__whitespaces_resistance():
    assert _parse_item_line("   1     egg    ") == (Quantity(1.0,Unit.UNIT), 'egg')


def test__parse_item_line__unit():
    assert _parse_item_line("12g ganja") == (Quantity(12.0,Unit.GRAM), 'ganja')


def test__parse_item_line__spaces_in_ingredient():
    assert _parse_item_line("12g sativa ganja") == (Quantity(12.0,Unit.GRAM), 'sativa ganja')


def test__parse_item_line__decimal_number():
    assert _parse_item_line("1.2g coke") == (Quantity(1.2,Unit.GRAM), 'coke')



def test__parse_item_line__debug():
    assert _parse_item_line("4.5kg oats") == (Quantity(4500.0,Unit.GRAM), 'oats')


def test__parse_item_line__unit_and_spaces():
    assert _parse_item_line("  12  g    ganja  ") == (Quantity(12.0,Unit.GRAM), 'ganja')


def test__parse_item_line__parenthesis():
    assert _parse_item_line("12g ganja (well dried)") == (Quantity(12.0,Unit.GRAM), 'ganja')


def test__parse_item_line__units():
    assert _parse_item_line("2kg rice") == (Quantity(2000.0,Unit.GRAM), 'rice')

def test__parse_item_line__float():
    assert _parse_item_line("2.5kg rice") == (Quantity(2500.0,Unit.GRAM), 'rice')


def test__parse_item_line__number_zero():
    with pytest.raises(ParsingError):
        _parse_item_line("0 apple")

def test__parse_item_line__no_number_zero():
    with pytest.raises(ParsingError):
        _parse_item_line("apple")


def test__parse_item_line__ingredient_starts_with_l():
    assert _parse_item_line("1 lemon") == (Quantity(1.0,Unit.UNIT), 'lemon')



# # ------------------------- parse recipe file -------------------------

PAN_CON_TOMATE_RECIPE_FILE = "tests/data/pan con tomate"
BOCATA_DE_NADA_RECIPE = "tests/data/bocata de nada"

def test__split_recipe_file():
    name, header, items, instructions = _split_recipe_file(PAN_CON_TOMATE_RECIPE_FILE)
    assert name == "pan con tomate"
    assert header.split("\n")==['serves: 2']
    assert items.split("\n")==['- 1 pan','- 100g tomate rallado']
    assert (
        instructions.split("\n")
        == ['grate the tomato', 'put it on the bread']
    )


def test__split_recipe_file__no_instructions():
    name, header, items, instructions = _split_recipe_file(BOCATA_DE_NADA_RECIPE)
    assert name == "bocata de nada"
    assert header.split("\n")==['serves: 1']
    assert items.split("\n")== ['- 1 pancito', '- 1l aire']
    assert instructions is None

def test__parse_recipe_file():
    name, header, items, instructions = parse_recipe_file(PAN_CON_TOMATE_RECIPE_FILE)
    assert header == {'serves': 2}
    assert items == [
        (Quantity(1.0,Unit.UNIT),'pan'),
        (Quantity(100.0,Unit.GRAM),"tomate rallado"),
    ]


def test__parse_recipe_file__no_instructions():
    name, header, items, instructions = parse_recipe_file(BOCATA_DE_NADA_RECIPE)
    assert header == {'serves': 1}
    assert items == [
        (Quantity(1.0,Unit.UNIT),'pancito'),
        (Quantity(1.0,Unit.LITER),"aire"),
    ]


