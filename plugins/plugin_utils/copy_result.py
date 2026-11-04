# Copyright: (c) 2024, Sardina Systems Ltd.
# SPDX-License-Identifier: Apache-2.0

"""Shared tail of the template-like action plugins: write the rendered result
to a local temporary file and hand it over to ``ansible.legacy.copy``."""

from __future__ import annotations

import os
import shutil
import tempfile
import typing

from ansible import constants as C
from ansible.module_utils.common.text.converters import to_bytes

if typing.TYPE_CHECKING:
    from ansible.plugins.action import ActionBase


def copy_rendered(
    action: ActionBase,
    task: typing.Any,
    *,
    content: str,
    filename: str,
    dest: str,
    task_vars: dict,
    follow: bool = True,
    encoding: str = "utf-8",
) -> dict:
    """Write ``content`` to a temp file named ``filename`` and run the copy
    action with ``task`` (a copy of the current task with the template-only
    arguments already removed). Returns the copy action result."""
    local_tempdir = tempfile.mkdtemp(dir=C.DEFAULT_LOCAL_TMP)
    try:
        result_file = os.path.join(local_tempdir, os.path.basename(filename))
        with open(to_bytes(result_file, errors="surrogate_or_strict"), "wb") as f:
            f.write(to_bytes(content, encoding=encoding, errors="surrogate_or_strict"))

        task.args.update(dict(src=result_file, dest=dest, follow=follow))

        # call with ansible.legacy prefix to eliminate collisions with collections while still allowing local override
        copy_action = action._shared_loader_obj.action_loader.get(
            "ansible.legacy.copy",
            task=task,
            connection=action._connection,
            play_context=action._play_context,
            loader=action._loader,
            templar=action._templar,
            shared_loader_obj=action._shared_loader_obj,
        )
        return copy_action.run(task_vars=task_vars)
    finally:
        shutil.rmtree(to_bytes(local_tempdir, errors="surrogate_or_strict"))
