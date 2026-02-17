"""
Test enabled Jinja test plugin
"""

import pytest
from jinja2.runtime import Undefined

from plugins.test import enabled as m


def test_enabled_scalar_bool_values():
    test = m.TestModule()

    assert test.is_enabled(True) is True
    assert test.is_enabled(False) is False


def test_enabled_list_values_all_true():
    test = m.TestModule()

    assert test.is_enabled([True, "yes", 1]) is True


def test_enabled_list_values_with_false():
    test = m.TestModule()

    assert test.is_enabled(["true", "false"]) is False


def test_enabled_undefined_uses_default():
    test = m.TestModule()

    assert test.is_enabled(Undefined(name="missing"), default=True) is True
    assert test.is_enabled(Undefined(name="missing"), default=False) is False


def test_enabled_scalar_string_true_raises_type_error_with_current_behavior():
    test = m.TestModule()

    with pytest.raises(TypeError):
        test.is_enabled("true")


def test_enabled_none_raises_type_error_with_current_behavior():
    test = m.TestModule()

    with pytest.raises(TypeError):
        test.is_enabled(None)
