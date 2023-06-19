import loader


def test__parse_item_line__no_unit():
    assert loader.parse_item_line("1 egg") == loader.ItemData(
        name="egg", number=1, unit=None
    )


def test__parse_item_line__case():
    assert loader.parse_item_line("1 EgG") == loader.ItemData(
        name="egg", number=1, unit=None
    )


def test__parse_item_line__whitespaces_resistance():
    assert loader.parse_item_line("   1     egg    ") == loader.ItemData(
        name="egg", number=1, unit=None
    )


def test__parse_item_line__unit():
    assert loader.parse_item_line("12g ganja") == loader.ItemData(
        name="ganja", number=12, unit="g"
    )


def test__parse_item_line__spaces_in_ingredient():
    assert loader.parse_item_line("12g sativa ganja") == loader.ItemData(
        name="sativa ganja", number=12, unit="g"
    )


def test__parse_item_line__unit_and_spaces():
    assert loader.parse_item_line("  12  g    ganja  ") == loader.ItemData(
        name="ganja", number=12, unit="g"
    )


def test__parse_item_line__parenthesis():
    assert loader.parse_item_line("12g ganja (well dried)") == loader.ItemData(
        name="ganja", number=12, unit="g"
    )


def test__parse_item_line__units():
    assert loader.parse_item_line("2kg rice") == loader.ItemData(
        name="rice", number=2, unit="kg"
    )
