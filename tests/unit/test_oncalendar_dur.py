"""
Test oncalendar_dur filter
"""

import pathlib
import sys

import pytest  # noqa
from ansible.errors import AnsibleFilterError  # noqa

actions_path = pathlib.Path(__file__).parent / ".." / ".." / "plugins" / "filter"
sys.path.insert(0, str(actions_path.absolute()))

import oncalendar_dur as m  # noqa

SPEC = "Mon,Thu,Sun *-*-* 01,13:00:00"


def test_oncalendar():
    dates = list(m.oncalendar(SPEC, iter_max=5))
    # print(dates)

    assert 5 == len(dates)


def test_oncalendar_dur():
    durs = list(m.oncalendar_dur(SPEC, iter_max=5))
    # print(durs)

    assert 43200.0 == min(durs)
    assert 216000.0 == max(durs)
