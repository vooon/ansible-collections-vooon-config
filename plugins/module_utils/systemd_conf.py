# Copyright: (c) 2024, Sardina Systems Ltd.
# SPDX-License-Identifier: Apache-2.0

"""Shared logic for modules that manage a single systemd config snippet
(``*.conf`` drop-in) in a ``*.d`` style directory."""

from __future__ import annotations

import typing
from pathlib import Path


def conf_path(directory: Path, name: str, suffix: str = ".conf") -> Path:
    """Return ``directory/name`` with ``suffix`` appended unless already present."""
    return directory / (name if name.endswith(suffix) else name + suffix)


def manage_conf_file(
    module,
    filepath: Path,
    *,
    state: str,
    content: str | None,
    directory_mode: typing.Any = None,
    validate: typing.Callable[[str], None] | None = None,
    apply: typing.Callable[[str], None] | None = None,
    remove_empty_dir: bool = False,
) -> dict:
    """Create, update or remove ``filepath`` and return ``changed`` and ``diff``.

    :param module: the ``AnsibleModule`` instance (check mode and file
        attributes are taken from it)
    :param state: ``present`` or ``absent``
    :param content: desired file content for ``present``
    :param directory_mode: if given, mode to enforce on the parent directory
    :param validate: called with the new content before it is written,
        also in check mode; raise/``fail_json`` to reject it
    :param apply: called with the new content after it has been written,
        never in check mode
    :param remove_empty_dir: on ``absent`` also remove the parent directory
        when it is left empty
    """
    changed = False
    diff = dict(before_header="", after_header="", before="", after="")

    if filepath.exists():
        diff["before_header"] = str(filepath)
        diff["before"] = filepath.read_text()

    if state == "present":
        if content is None:
            module.fail_json(msg="content is required when state=present")
        else:
            changed = _ensure_present(
                module,
                filepath,
                content,
                diff,
                directory_mode=directory_mode,
                validate=validate,
                apply=apply,
            )
    elif state == "absent":
        changed = _ensure_absent(module, filepath, remove_empty_dir=remove_empty_dir)
    else:
        module.fail_json(msg=f"unsupported state: {state}")

    return dict(changed=changed, diff=diff)


def _ensure_present(
    module,
    filepath: Path,
    content: str,
    diff: dict,
    *,
    directory_mode: typing.Any,
    validate: typing.Callable[[str], None] | None,
    apply: typing.Callable[[str], None] | None,
) -> bool:
    dirpath = filepath.parent
    changed = False

    if not dirpath.exists():
        changed = True
        if not module.check_mode:
            dirpath.mkdir(mode=0o755, parents=True)

    if directory_mode is not None and dirpath.exists():
        changed = module.set_mode_if_different(str(dirpath), directory_mode, changed)

    diff["after_header"] = str(filepath)
    diff["after"] = content
    if not filepath.exists() or diff["before"] != content:
        if validate is not None:
            validate(content)

        changed = True
        if not module.check_mode:
            filepath.write_bytes(content.encode("utf-8"))
            if apply is not None:
                apply(content)

    if filepath.exists():
        file_args = module.load_file_common_arguments(module.params, path=str(filepath))
        changed = module.set_fs_attributes_if_different(file_args, changed)

    return changed


def _ensure_absent(module, filepath: Path, *, remove_empty_dir: bool) -> bool:
    dirpath = filepath.parent
    changed = False

    if filepath.exists():
        changed = True
        if not module.check_mode:
            filepath.unlink()

    if remove_empty_dir and dirpath.exists():
        # In check mode the file is still there; the directory counts as
        # empty when that file is the only entry.
        remaining = [p for p in dirpath.iterdir() if p != filepath]
        if not remaining and (module.check_mode or not filepath.exists()):
            changed = True
            if not module.check_mode:
                dirpath.rmdir()

    return changed
