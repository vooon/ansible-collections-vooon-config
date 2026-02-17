# -*- coding: utf-8 -*-
# Copyright: (c) 2024, Sardina Systems Ltd.
# SPDX-License-Identifier: Apache-2.0

import datetime as dt
import typing

from ansible.errors import AnsibleFilterTypeError

try:
    from oncalendar import OnCalendar
except ImportError:
    OnCalendar = None  # type: ignore[assignment,misc]


def oncalendar(
    spec: str,
    start_time: typing.Union[dt.datetime, str, None] = None,
    tz: dt.tzinfo = dt.UTC,
    iter_max: int = 0,
) -> typing.Iterable[dt.datetime]:
    """Parse systemd OnCalendar spec and return to stream of next invocation dates"""

    if OnCalendar is None:
        raise AnsibleFilterTypeError("oncalendar python package is required")

    if isinstance(start_time, str):
        start_time = dt.datetime.fromisoformat(start_time)
    if start_time is None:
        start_time = dt.datetime.now(tz=tz)

    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=tz)

    it = OnCalendar(spec, start_time)

    if iter_max <= 0:
        return it

    for _count in range(iter_max):
        try:
            yield next(it)
        except StopIteration:
            return


def oncalendar_dur(
    spec: str,
    start_time: typing.Union[dt.datetime, str, None] = None,
    tz: dt.tzinfo = dt.UTC,
    iter_max: int = 0,
) -> typing.Iterable[float]:
    """Parse systemd OnCalendar spec and return time deltas between dates in seconds"""

    if iter_max > 0:
        iter_max += 1

    it = iter(oncalendar(spec, start_time, tz, iter_max))

    try:
        prev = next(it)
    except StopIteration:
        return
    for new in it:
        d: dt.timedelta = new - prev
        yield d.total_seconds()
        prev = new


class FilterModule:
    """Ansible argsenvfmt jinja2 filters"""

    def filters(self):
        return {
            "oncalendar": oncalendar,
            "oncalendar_dur": oncalendar_dur,
        }
