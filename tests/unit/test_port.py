"""
Test port/add_port filters
"""

import pytest
from ansible.errors import AnsibleFilterError, AnsibleFilterTypeError
from jinja2.exceptions import UndefinedError

from plugins.filter import port as m


class DummyContext:
    def __init__(self, variables):
        self._vars = variables

    def resolve(self, name):
        if name in self._vars:
            return self._vars[name]
        raise UndefinedError(name)


def test_port_prefers_overrides():
    ctx = DummyContext(
        {
            "ports": {"api": {"bind": 123}},
            "ports_overrides": {"api": {"bind": 321}},
        }
    )

    assert m.port(ctx, "api.bind") == 321


def test_port_falls_back_to_alt_suffix():
    ctx = DummyContext(
        {
            "ports": {"api": {"bind_port": 123}},
            "ports_overrides": {},
        }
    )

    assert m.port(ctx, "api.bind") == 123


def test_port_key_type_error():
    ctx = DummyContext({"ports": {}})

    with pytest.raises(AnsibleFilterTypeError):
        m.port(ctx, 1)  # type: ignore[arg-type]


def test_port_bad_key_format_error():
    ctx = DummyContext({"ports": {"api": {"bind": 123}}})

    with pytest.raises(AnsibleFilterError):
        m.port(ctx, "api")


def test_add_port_single_host():
    ctx = DummyContext({"ports": {"api": {"bind": 123}}})

    assert m.add_port(ctx, "127.0.0.1", "api.bind") == "127.0.0.1:123"


def test_add_port_iterable_hosts():
    ctx = DummyContext({"ports": {"api": {"bind": 123}}})

    out = list(m.add_port(ctx, ["127.0.0.1", "0.0.0.0"], "api.bind"))
    assert out == ["127.0.0.1:123", "0.0.0.0:123"]
