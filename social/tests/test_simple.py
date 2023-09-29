def test_add():
    assert 1 + 1 == 2


def test_dict_contains():
    dict_x = {"a": 1, "b": 2}

    expected = {"a": 1}

    assert expected.items() <= dict_x.items()
