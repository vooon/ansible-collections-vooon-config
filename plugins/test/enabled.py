# -*- coding: utf-8 -*-

import typing
from collections.abc import Iterable

from ansible.module_utils.parsing.convert_bool import boolean
from jinja2.runtime import Undefined

WhenConvertible = typing.Union[None, str, bool]
WhenArg = typing.Union[WhenConvertible, typing.List[WhenConvertible]]


class TestModule(object):
    """Ansible tests"""

    def tests(self):
        return {
            "enabled": self.is_enabled,
        }

    def is_enabled(self, value: WhenArg, default: bool = True) -> bool:
        """Return True if value is a Conditional (when) and all true"""

        if isinstance(value, Undefined):
            value = [default]

        # convert anything to list
        if not isinstance(value, Iterable):
            value = [value]

        return all(boolean(v) for v in value)
