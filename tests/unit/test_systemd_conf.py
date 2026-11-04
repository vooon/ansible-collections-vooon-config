# Copyright: (c) 2024, Sardina Systems Ltd.
# SPDX-License-Identifier: Apache-2.0

"""
Test the shared systemd_conf module_utils helper with a fake AnsibleModule.
"""

import pathlib
import sys

import pytest

utils_path = pathlib.Path(__file__).parent / ".." / ".." / "plugins" / "module_utils"
sys.path.insert(0, str(utils_path.absolute()))

import systemd_conf as m


class FakeModule:
    """Just enough of AnsibleModule for manage_conf_file."""

    def __init__(self, check_mode=False, params=None):
        self.check_mode = check_mode
        self.params = params or {}
        self.calls: list[tuple] = []
        self.failed: str | None = None

    def fail_json(self, **kwargs):
        self.failed = kwargs.get("msg")
        raise SystemExit(1)

    def set_mode_if_different(self, path, mode, changed):
        self.calls.append(("set_mode", path, mode))
        return changed

    def load_file_common_arguments(self, params, path=None):
        self.calls.append(("load_file_args", path))
        return dict(path=path, mode=params.get("mode"))

    def set_fs_attributes_if_different(self, file_args, changed):
        self.calls.append(("set_fs_attrs", file_args["path"]))
        return changed


def test_conf_path_appends_suffix_once():
    d = pathlib.Path("/etc/x.d")

    assert m.conf_path(d, "foo") == d / "foo.conf"
    assert m.conf_path(d, "foo.conf") == d / "foo.conf"
    assert m.conf_path(d, "unit.service", suffix=".d") == d / "unit.service.d"


def test_present_creates_dir_and_file(tmp_path):
    module = FakeModule(params={"mode": "0644"})
    filepath = tmp_path / "sub" / "foo.conf"
    validated, applied = [], []

    res = m.manage_conf_file(
        module,
        filepath,
        state="present",
        content="x=1\n",
        validate=validated.append,
        apply=applied.append,
    )

    assert res["changed"] is True
    assert filepath.read_text() == "x=1\n"
    assert res["diff"]["before"] == ""
    assert res["diff"]["after"] == "x=1\n"
    assert validated == ["x=1\n"]
    assert applied == ["x=1\n"]
    assert ("set_fs_attrs", str(filepath)) in module.calls


def test_present_is_idempotent(tmp_path):
    module = FakeModule()
    filepath = tmp_path / "foo.conf"
    filepath.write_text("x=1\n")
    validated, applied = [], []

    res = m.manage_conf_file(
        module,
        filepath,
        state="present",
        content="x=1\n",
        validate=validated.append,
        apply=applied.append,
    )

    assert res["changed"] is False
    assert res["diff"]["before"] == res["diff"]["after"] == "x=1\n"
    assert validated == []
    assert applied == []


def test_present_check_mode_validates_but_does_not_write(tmp_path):
    module = FakeModule(check_mode=True)
    filepath = tmp_path / "sub" / "foo.conf"
    validated, applied = [], []

    res = m.manage_conf_file(
        module,
        filepath,
        state="present",
        content="x=1\n",
        validate=validated.append,
        apply=applied.append,
    )

    assert res["changed"] is True
    assert not filepath.parent.exists()
    assert validated == ["x=1\n"]
    assert applied == []


def test_present_enforces_directory_mode(tmp_path):
    module = FakeModule()
    filepath = tmp_path / "unit.d" / "foo.conf"

    m.manage_conf_file(
        module, filepath, state="present", content="x\n", directory_mode="0750"
    )

    assert ("set_mode", str(filepath.parent), "0750") in module.calls


def test_present_without_content_fails():
    module = FakeModule()

    with pytest.raises(SystemExit):
        m.manage_conf_file(
            module, pathlib.Path("/nonexistent/foo.conf"), state="present", content=None
        )

    assert module.failed is not None


def test_absent_removes_file_and_empty_dir(tmp_path):
    module = FakeModule()
    filepath = tmp_path / "unit.d" / "foo.conf"
    filepath.parent.mkdir()
    filepath.write_text("x\n")

    res = m.manage_conf_file(
        module, filepath, state="absent", content=None, remove_empty_dir=True
    )

    assert res["changed"] is True
    assert res["diff"]["before"] == "x\n"
    assert not filepath.parent.exists()


def test_absent_keeps_dir_with_other_files(tmp_path):
    module = FakeModule()
    filepath = tmp_path / "unit.d" / "foo.conf"
    filepath.parent.mkdir()
    filepath.write_text("x\n")
    (filepath.parent / "other.conf").write_text("y\n")

    m.manage_conf_file(
        module, filepath, state="absent", content=None, remove_empty_dir=True
    )

    assert not filepath.exists()
    assert filepath.parent.exists()


def test_absent_check_mode_reports_dir_removal(tmp_path):
    module = FakeModule(check_mode=True)
    filepath = tmp_path / "unit.d" / "foo.conf"
    filepath.parent.mkdir()
    filepath.write_text("x\n")

    res = m.manage_conf_file(
        module, filepath, state="absent", content=None, remove_empty_dir=True
    )

    assert res["changed"] is True
    assert filepath.exists()


def test_absent_is_idempotent(tmp_path):
    module = FakeModule()

    res = m.manage_conf_file(
        module, tmp_path / "foo.conf", state="absent", content=None
    )

    assert res["changed"] is False
