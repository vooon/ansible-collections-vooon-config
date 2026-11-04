# Copyright: (c) 2024, Sardina Systems Ltd.
# SPDX-License-Identifier: Apache-2.0


from collections.abc import Iterable

from ansible.module_utils.parsing.convert_bool import boolean
from ansible.template import accept_args_markers
from jinja2.runtime import Undefined

try:
    # Private API, but the only way to tell "undefined" apart from other
    # deferred errors (ansible-core >= 2.19 templating engine).
    from ansible._internal._templating._jinja_common import Marker, UndefinedMarker
except ImportError:  # pragma: no cover
    Marker = UndefinedMarker = Undefined  # type: ignore[misc,assignment]

WhenConvertible = None | str | bool
WhenArg = WhenConvertible | list[WhenConvertible]


class TestModule:
    """Ansible tests"""

    def tests(self):
        return {
            "enabled": self.is_enabled,
        }

    # Without this the templating engine never calls the test for an undefined
    # input: it short-circuits and the `when` fails with an undefined error.
    @accept_args_markers
    def is_enabled(self, value: WhenArg, default: bool = True) -> bool:
        """Return True if value is a Conditional (when) and all true"""

        if isinstance(value, Marker) and not isinstance(value, UndefinedMarker):
            # Some other deferred error (e.g. a failed nested template); re-raise it.
            value.trip()

        if isinstance(value, Undefined):
            value = [default]

        # convert anything to list; a string is a single value
        if isinstance(value, str) or not isinstance(value, Iterable):
            value = [value]

        return all(boolean(v) for v in value)
