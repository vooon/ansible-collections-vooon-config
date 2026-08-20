# Copyright: (c) 2024, Sardina Systems Ltd.
# SPDX-License-Identifier: Apache-2.0

"""
Test config_template action rendering of json/yaml/toml/ini config types.

These tests exercise the action plugin's config-type mergers together with
Jinja variable rendering. They mirror how the plugin prepares the template data
internally (mark it trusted, then template with a fresh Templar).
"""

import pathlib
import sys

actions_path = pathlib.Path(__file__).parent / ".." / ".." / "plugins" / "action"
sys.path.insert(0, str(actions_path.absolute()))

import config_template
import pytest
from ansible.parsing.dataloader import DataLoader
from ansible.plugins.action.template import trust_as_template
from ansible.template import Templar

VARS = {
    "name": "demo",
    "port": 8080,
    "enabled": True,
    "items": ["a", "b"],
}


@pytest.fixture(scope="module")
def action():
    # Bypass ActionBase init; the merger methods only rely on their args.
    return config_template.ActionModule.__new__(config_template.ActionModule)


def _render(data: str, variables: dict) -> str:
    loader = DataLoader()
    templar = Templar(loader=loader, variables=variables)
    templar = templar.copy_with_new_env(available_variables=variables)
    return templar.template(
        trust_as_template(data),
        preserve_trailing_newlines=True,
        escape_backslashes=False,
        overrides=None,
    )


def _args(overrides: dict, config_type: str, **kwargs) -> config_template.TaskArgs:
    args = config_template.TaskArgs()
    args.source = "test"
    args.config_type = config_type
    args.config_overrides = overrides
    args._patcher = config_template.SimpleMerger(
        new_items=overrides,
        list_extend=kwargs.get("list_extend", False),
        yml_multilines=kwargs.get("yml_multilines", False),
    )
    return args


def test_render_resolves_variables_when_trusted():
    """The regression test for ansible-core 2.19+ trust checks.

    Without marking the template data as trusted, the ansible-core templating
    engine refuses to render it and returns ``{{ var }}`` unchanged.
    """
    rendered = _render("value = {{ name }}\n", VARS)
    assert rendered == "value = demo\n"
    assert "{{" not in rendered


def test_render_leaves_variables_unresolved_when_untrusted():
    # Demonstrates the bug: untrusted data is returned unrendered.
    loader = DataLoader()
    templar = Templar(loader=loader, variables=VARS)
    templar = templar.copy_with_new_env(available_variables=VARS)
    out = templar.template(
        "value = {{ name }}\n",
        preserve_trailing_newlines=True,
        escape_backslashes=False,
        overrides=None,
    )
    assert out == "value = {{ name }}\n"


@pytest.mark.parametrize(
    "config_type,base,overrides,expected_merged",
    [
        (
            "json",
            '{"name": "{{ name }}", "port": {{ port }}}',
            {"port": 9090},
            {"name": "demo", "port": 9090},
        ),
        (
            "yaml",
            "name: {{ name }}\nport: {{ port }}\n",
            {"port": 9090},
            {"name": "demo", "port": 9090},
        ),
        (
            "toml",
            'name = "{{ name }}"\nport = {{ port }}\n',
            {"port": 9090},
            {"name": "demo", "port": 9090},
        ),
    ],
)
def test_config_types_merge_and_render(
    action, config_type, base, overrides, expected_merged
):
    rendered = _render(base, VARS)
    merged = action.type_merger(rendered, _args(overrides, config_type))
    resultant, config_base = merged

    assert "{{" not in resultant
    assert config_base == expected_merged


def test_json_config_type(action):
    rendered = _render('{"name": "{{ name }}", "items": ["base"]}', VARS)
    args = _args({"port": 9090}, "json")
    resultant, config_base = action.return_config_overrides_json(
        rendered, args, __import__("json").loads
    )

    assert (
        __import__("json").loads(resultant)
        == config_base
        == {
            "name": "demo",
            "port": 9090,
            "items": ["base"],
        }
    )


def test_ini_config_type(action):
    base = "[section]\nname = {{ name }}\nenabled = {{ enabled }}\n"
    rendered = _render(base, VARS)
    args = _args({"name": "overridden"}, "ini")
    resultant, config_base = action.return_config_overrides_ini(rendered, args)

    assert "{{" not in resultant
    assert "[section]" in resultant
    assert "name = overridden" in resultant
    assert config_base["section"]["enabled"] == "True"


def test_ini_list_override_joins_with_separator(action):
    rendered = "[section]\nitems = X\n"
    args = _args({"items": ["x", "y"]}, "ini")
    resultant = action.return_config_overrides_ini(rendered, args)[0]

    assert "items = x,y" in resultant


def test_list_extend_appends_rendered_list(action):
    rendered = _render('{"items": ["a", "b"]}', VARS)
    args = _args({"items": ["z"]}, "json", list_extend=True)
    resultant, config_base = action.return_config_overrides_json(
        rendered, args, __import__("json").loads
    )

    assert __import__("json").loads(resultant)["items"] == ["a", "b", "z"]
    assert config_base["items"] == ["a", "b", "z"]


def test_list_extend_false_replaces_list(action):
    rendered = _render('{"items": ["a", "b"]}', VARS)
    args = _args({"items": ["z"]}, "json", list_extend=False)
    resultant, config_base = action.return_config_overrides_json(
        rendered, args, __import__("json").loads
    )

    assert __import__("json").loads(resultant)["items"] == ["z"]
    assert config_base["items"] == ["z"]


def test_strip_ansible_tags_converts_tagged_scalars():
    class TagInt(int):
        pass

    class TagStr(str):
        pass

    value = {
        "port": TagInt(9090),
        "name": TagStr("demo"),
        "flag": True,
        "nested": {"x": TagInt(1)},
    }
    out = config_template._strip_ansible_tags(value)

    assert out["port"].__class__ is int and out["port"] == 9090
    assert out["name"].__class__ is str and out["name"] == "demo"
    assert out["flag"].__class__ is bool and out["flag"] is True
    assert out["nested"]["x"].__class__ is int


def test_strip_ansible_tags_preserves_ruamel_roundtrip_nodes():
    from io import StringIO

    from ruamel.yaml import YAML

    yaml = YAML(typ="rt")
    yaml.default_flow_style = False
    node = yaml.load(StringIO("# keep me\nport: 8080\n"))

    from ruamel.yaml.comments import CommentedMap

    assert isinstance(node, CommentedMap)
    out = config_template._strip_ansible_tags(node)

    # Same object mutated in place (comments preserved), scalar left untouched.
    assert out is node
    assert out["port"].__class__ is int
