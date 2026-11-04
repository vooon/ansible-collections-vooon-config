# Copyright: (c) 2024, Sardina Systems Ltd.
# SPDX-License-Identifier: Apache-2.0

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


@pytest.mark.parametrize(
    "value, expected",
    [("true", True), ("yes", True), ("on", True), ("false", False), ("no", False)],
)
def test_enabled_scalar_string(value, expected):
    test = m.TestModule()

    assert test.is_enabled(value) is expected


def test_enabled_none_raises_type_error_with_current_behavior():
    test = m.TestModule()

    with pytest.raises(TypeError):
        test.is_enabled(None)


def test_enabled_undefined_marker_uses_default():
    from ansible._internal._templating._jinja_common import UndefinedMarker

    test = m.TestModule()
    marker = UndefinedMarker(name="missing", _no_template_source=True)

    assert test.is_enabled(marker) is True
    assert test.is_enabled(marker, default=False) is False


def test_enabled_other_marker_is_tripped():
    from ansible._internal._templating._jinja_common import Marker, MarkerError

    test = m.TestModule()
    # A non-undefined marker (e.g. a captured exception) must be re-raised.
    marker = Marker(hint="boom", _no_template_source=True)

    with pytest.raises(MarkerError):
        test.is_enabled(marker)


def test_enabled_accepts_args_markers():
    test = m.TestModule()

    assert getattr(test.tests()["enabled"], "accept_args_markers", False) is True
