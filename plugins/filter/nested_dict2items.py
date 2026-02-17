# -*- coding: utf-8 -*-
# Copyright: (c) 2024, Sardina Systems Ltd.
# SPDX-License-Identifier: Apache-2.0

import typing
from collections.abc import Mapping

from ansible.errors import AnsibleFilterError


def nested_dict2items(
    inp: typing.Dict[str, typing.Dict[str, typing.Any]],
    expected_depth: int = -1,
) -> typing.Iterator[typing.Tuple]:
    """Recursively walks trough dict of dicts and returns tuple of as many items as many levels of nesting you have"""

    def recursive_down(d, parent=()):
        for k, v in d.items():
            p = parent + (dict(key=k, value=v),)

            if isinstance(v, Mapping):
                for vv in recursive_down(v, p):
                    yield vv

            else:
                yield p

    for vv in recursive_down(inp, ()):
        if expected_depth >= 0 and len(vv) != expected_depth:
            raise AnsibleFilterError(
                f"Item depth doesn't match expected: {len(vv)} != {expected_depth}, item: {vv}"
            )

        yield vv


class FilterModule:
    """Ansible nested_dict2items jinja2 filters"""

    def filters(self):
        return {
            "nested_dict2items": nested_dict2items,
        }
