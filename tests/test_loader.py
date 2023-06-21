from planner import models


def test__parse_item_line__no_unit():
    assert models.Item.parse_item_line("1 egg") == ("egg", 1, None)


def test__parse_item_line__case():
    assert models.Item.parse_item_line("1 EgG") == ("egg", 1, None)


def test__parse_item_line__whitespaces_resistance():
    assert models.Item.parse_item_line("   1     egg    ") == ("egg", 1, None)


def test__parse_item_line__unit():
    assert models.Item.parse_item_line("12g ganja") == ("ganja", 12, "g")


def test__parse_item_line__spaces_in_ingredient():
    assert models.Item.parse_item_line("12g sativa ganja") == ("sativa ganja", 12, "g")


def test__parse_item_line__unit_and_spaces():
    assert models.Item.parse_item_line("  12  g    ganja  ") == ("ganja", 12, "g")


def test__parse_item_line__parenthesis():
    assert models.Item.parse_item_line("12g ganja (well dried)") == ("ganja", 12, "g")


def test__parse_item_line__units():
    assert models.Item.parse_item_line("2kg rice") == ("rice", 2, "kg")
