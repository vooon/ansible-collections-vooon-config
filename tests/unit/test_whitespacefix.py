# Copyright: (c) 2024, Sardina Systems Ltd.
# SPDX-License-Identifier: Apache-2.0

"""
Test whitespacefix filter
"""

from plugins.filter import whitespacefix as m


def test_whitespacefix_collapses_empty_lines_and_rstrip():
    text = "foo  \n\n\nbar\n   \n baz  \n"

    out = m.whitespacefix(text)

    assert out == "foo\n\nbar\n\n baz"


def test_whitespacefix_keeps_single_blank_line():
    text = "a\n\nb\n"

    out = m.whitespacefix(text)

    assert out == "a\n\nb"
