# Copyright: (c) 2024, Sardina Systems Ltd.
# SPDX-License-Identifier: Apache-2.0


import typing
from collections.abc import Iterable
from datetime import timedelta

from ansible.errors import AnsibleTypeError

try:
    import durationpy
except ImportError:
    durationpy = None  # type: ignore[assignment]

_StrOrList = str | typing.Iterable[str]
_Number = int | float
_FloatOrList = _Number | typing.Iterable[_Number]


def dur2sec(dur: _StrOrList) -> _FloatOrList:
    if durationpy is None:
        raise AnsibleTypeError("durationpy python package is required")

    if not isinstance(dur, (str, Iterable)):
        raise AnsibleTypeError(f"dur should be string or list, got: {dur!r}")

    if isinstance(dur, str):
        td = durationpy.from_str(dur)
        return td.total_seconds()

    return (dur2sec(d2) for d2 in dur)  # type: ignore


def sec2dur(sec: _FloatOrList) -> _StrOrList:
    if durationpy is None:
        raise AnsibleTypeError("durationpy python package is required")

    if isinstance(sec, bool) or not isinstance(sec, (int, float, Iterable)):
        raise AnsibleTypeError(f"sec should be a number or list, got: {sec!r}")

    if isinstance(sec, (int, float)):
        return durationpy.to_str(timedelta(seconds=sec))

    return (sec2dur(s2) for s2 in sec)  # type: ignore


class FilterModule:
    """Ansible duration jinja2 filters"""

    def filters(self):
        return {
            "dur2sec": dur2sec,
            "sec2dur": sec2dur,
        }
