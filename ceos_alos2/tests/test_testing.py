import pytest

from ceos_alos2 import testing


@pytest.mark.parametrize("b", ({"a": 1}, {"c": 1}, {"a": 1, "c": 1}))
@pytest.mark.parametrize("a", ({"a": 1}, {"b": 1}, {"a": 1, "b": 1}))
def test_dict_overlap(a, b):
    missing_left, common, missing_right = testing.dict_overlap(a, b)

    assert set(a) == set(missing_right) | set(common)
    assert set(b) == set(missing_left) | set(common)

    assert all(k in a and k in b for k in common)
    assert all(k not in a and k in b for k in missing_left)
    assert all(k in a and k not in b for k in missing_right)


@pytest.mark.parametrize("keys", (["ab"], ["ab", "cd"]))
@pytest.mark.parametrize("side", ("left", "right"))
def test_diff_mapping_missing(keys, side):
    diff = testing.diff_mapping_missing(keys, side)

    assert side in diff
    assert all(f"- {key}" in diff for key in keys)


@pytest.mark.parametrize("name", ("attributes", "variables", "groups"))
@pytest.mark.parametrize(
    ["left", "right", "unequal"],
    (
        pytest.param({"a": 1, "b": 2}, {"a": 1, "b": 3}, ["b"]),
        pytest.param({"a": 2, "b": 2}, {"a": 1, "b": 3}, ["a", "b"]),
        pytest.param({"c": 1, "e": 5}, {"c": 2, "e": 2}, ["c", "e"]),
    ),
)
def test_diff_mapping_not_equal(left, right, unequal, name):
    actual = testing.diff_mapping_not_equal(left, right, name=name)

    assert actual.startswith(f"Differing {name}")
    assert all(f"L {k} " in actual and f"R {k} " in actual for k in unequal)


@pytest.mark.parametrize("name", ("Attributes", "Variables", "Groups"))
@pytest.mark.parametrize(
    ["left", "right", "missing_left", "common_unequal", "missing_right"],
    (
        pytest.param({"b": 2}, {"b": 2, "c": 3}, True, False, False, id="missing_left"),
        pytest.param({"a": 1, "b": 2}, {"b": 2}, False, False, True, id="missing_right"),
        pytest.param({"b": 2}, {"b": 3}, False, True, False, id="unequal_common"),
        pytest.param({"b": 2}, {"b": 2}, False, False, False, id="all_equal"),
        pytest.param(
            {"b": 2}, {"b": 3, "c": 3}, True, True, False, id="unequal_common-missing_left"
        ),
        pytest.param(
            {"a": 1, "b": 2}, {"b": 3}, False, True, True, id="unequal_common-missing_right"
        ),
        pytest.param({"a": 1, "b": 2}, {"b": 3, "c": 3}, True, True, True, id="all_different"),
    ),
)
def test_diff_mapping(left, right, missing_left, common_unequal, missing_right, name):
    actual = testing.diff_mapping(left, right, name=name)

    assert actual.startswith(name)
    assert not missing_left or "Missing left" in actual
    assert not common_unequal or f"Differing {name.lower()}" in actual
    assert not missing_right or "Missing right" in actual


@pytest.mark.parametrize("name", ["name1", "Name2"])
@pytest.mark.parametrize(["left", "right"], [(1, 2), ("a", "b")])
def test_diff_scalar(left, right, name):
    actual = testing.diff_scalar(left, right, name=name)

    assert name.title() in actual
    assert f"L  {left}" in actual
    assert f"R  {right}" in actual
