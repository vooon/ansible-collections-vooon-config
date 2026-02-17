"""
Test url_replace filter
"""

from plugins.filter import urlreplace as m


class DummyContext:
    def __init__(self, variables):
        self._vars = variables

    def resolve(self, name):
        return self._vars[name]


def test_url_replace_pathadd():
    ctx = DummyContext({"ports": {"api": {"bind": 123}}})

    out = m.url_replace(ctx, "http://example.com/foo", pathadd="bar")

    assert out == "http://example.com/foo/bar"


def test_url_replace_path_and_scheme():
    ctx = DummyContext({"ports": {"api": {"bind": 123}}})

    out = m.url_replace(ctx, "http://example.com/ws", path="/api", scheme="wss")

    assert out == "wss://example.com/api"


def test_url_replace_port_by_key():
    ctx = DummyContext(
        {
            "ports": {"api": {"bind": 123}},
            "ports_overrides": {"api": {"bind": 321}},
        }
    )

    out = m.url_replace(ctx, "http://example.com/api", port="api.bind")

    assert out == "http://example.com:321/api"


def test_url_replace_remove_port_with_none():
    ctx = DummyContext({"ports": {"api": {"bind": 123}}})

    out = m.url_replace(ctx, "http://example.com:8080/api", port=None)

    assert out == "http://example.com/api"
