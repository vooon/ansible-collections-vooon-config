# Copyright: (c) 2024, Sardina Systems Ltd.
# SPDX-License-Identifier: Apache-2.0

"""
Test duration_go filters
"""

import pytest
from ansible.errors import AnsibleFilterTypeError

from plugins.filter import duration_go as m


def test_dur2sec_single_value():
    assert m.dur2sec("2h30m") == 9000.0


def test_dur2sec_iterable_values():
    out = list(m.dur2sec(["1m", "2m"]))
    assert out == [60.0, 120.0]


def test_dur2sec_type_error():
    with pytest.raises(AnsibleFilterTypeError):
        m.dur2sec(123)  # type: ignore[arg-type]


def test_sec2dur_single_value():
    assert m.sec2dur(600.0) == "10m"


def test_sec2dur_iterable_values():
    out = list(m.sec2dur([60.0, 120.0]))
    assert out == ["1m", "2m"]


def test_sec2dur_type_error():
    with pytest.raises(AnsibleFilterTypeError):
        m.sec2dur(1)  # type: ignore[arg-type]
