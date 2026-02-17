"""
Test argsenvfmt filter
"""

from plugins.filter import argsenvfmt as m


class DummyContext:
    def __init__(self):
        self.environment = type(
            "DummyEnv",
            (),
            {"filters": {"quote": lambda value: f"<{value}>"}},
        )()


def test_argsenvfmt_single_line_unquoted():
    ctx = DummyContext()
    text = """
      --foo

      --bar baz
    """

    out = m.argsenvfmt(ctx, text, quote=False, multiline=False)

    assert out == "--foo --bar baz"


def test_argsenvfmt_single_line_quoted():
    ctx = DummyContext()
    text = "--foo\n--bar"

    out = m.argsenvfmt(ctx, text, quote=True, multiline=False)

    assert out == "<--foo --bar>"


def test_argsenvfmt_multiline_quotes_embedded_quotes():
    ctx = DummyContext()
    text = '--foo\n--label="abc"\n'

    out = m.argsenvfmt(ctx, text, quote=True, multiline=True)

    assert out.startswith('"\\\n')
    assert '--label=\\"abc\\" \\\n' in out
    assert out.endswith('"')
