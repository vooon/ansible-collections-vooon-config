# Copyright: (c) 2024, Sardina Systems Ltd.
# SPDX-License-Identifier: Apache-2.0

"""
Test commentif filter
"""

from plugins.filter import commentif as m


class DummyContext:
    def __init__(self):
        self.environment = type(
            "DummyEnv",
            (),
            {
                "filters": {
                    "comment": lambda text, style, **kw: (
                        f"[{style}] {text} {kw.get('decoration', '')}".strip()
                    )
                }
            },
        )()


def test_commentif_applies_comment_filter_when_true():
    ctx = DummyContext()

    out = m.commentif(ctx, "hello", cond=True, style="plain", decoration="!")

    assert out == "[plain] hello !"


def test_commentif_returns_original_text_when_false():
    ctx = DummyContext()

    out = m.commentif(ctx, "hello", cond=False)

    assert out == "hello"
