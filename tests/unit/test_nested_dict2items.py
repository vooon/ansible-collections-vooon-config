"""
Test nested_dict2items filter
"""

import pathlib
import sys

import pytest
from ansible.errors import AnsibleFilterError  # noqa

actions_path = pathlib.Path(__file__).parent / ".." / ".." / "plugins" / "filter"
sys.path.insert(0, str(actions_path.absolute()))

import nested_dict2items as m  # noqa


@pytest.mark.parametrize(
    "inp,expected",
    [
        (
            dict(mon=dict()),
            [],
        ),
        (
            dict(mon=dict(foo="bar")),
            [
                (
                    dict(key="mon", value=dict(foo="bar")),
                    dict(key="foo", value="bar"),
                )
            ],
        ),
        (
            dict(mon=dict(foo=dict(bar="baz"))),
            [
                (
                    dict(key="mon", value=dict(foo=dict(bar="baz"))),
                    dict(key="foo", value=dict(bar="baz")),
                    dict(key="bar", value="baz"),
                )
            ],
        ),
    ],
)
def test_nested_dict2items(inp, expected):
    obtained = list(m.nested_dict2items(inp))
    assert obtained == expected


def test_nested_dict2items_depth_check():
    with pytest.raises(AnsibleFilterError):
        # NOTE: list required to make all calls on generator
        list(
            m.nested_dict2items(
                dict(mon=dict(foo=dict(bar="baz"))),
                expected_depth=2,
            )
        )
