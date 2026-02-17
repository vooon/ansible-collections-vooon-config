# Copyright: (c) 2024, Sardina Systems Ltd.
# SPDX-License-Identifier: Apache-2.0

"""
Test jsonnet module/action plugin basics
"""

from pathlib import Path

import pytest
import yaml
from ansible.errors import AnsibleError

from plugins.action import jsonnet as action_jsonnet
from plugins.modules import jsonnet as module_jsonnet


def test_jsonnet_module_documentation_schema():
    doc = yaml.safe_load(module_jsonnet.DOCUMENTATION)

    assert doc["module"] == "jsonnet"
    assert doc["version_added"] == "2.6.0"
    assert sorted(doc["options"]["format"]["choices"]) == ["json", "yaml"]


def test_import_callback_returns_file_content(tmp_path: Path):
    include_dir = tmp_path / "include"
    include_dir.mkdir()
    target = include_dir / "common.libsonnet"
    target.write_bytes(b"{ x: 1 }")

    module = action_jsonnet.ActionModule.__new__(action_jsonnet.ActionModule)

    def find_needle(base: str, rel: str) -> str:
        candidate = Path(base) / rel
        if candidate.exists():
            return str(candidate)
        raise AnsibleError(f"not found: {candidate}")

    module._find_needle = find_needle  # type: ignore[attr-defined]

    full_path, content = module.import_callback([str(include_dir)], "common.libsonnet")

    assert full_path == str(target)
    assert content == b"{ x: 1 }"


def test_import_callback_raises_when_missing(tmp_path: Path):
    module = action_jsonnet.ActionModule.__new__(action_jsonnet.ActionModule)

    def find_needle(base: str, rel: str) -> str:
        raise AnsibleError(f"not found: {base}/{rel}")

    module._find_needle = find_needle  # type: ignore[attr-defined]

    with pytest.raises(AnsibleError, match="Unable to find"):
        module.import_callback([str(tmp_path)], "missing.libsonnet")
