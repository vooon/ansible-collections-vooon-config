# Copyright: (c) 2024, Sardina Systems Ltd.
# SPDX-License-Identifier: Apache-2.0

"""Make ``ansible_collections.vooon.config`` resolve to this working tree.

Plugins import shared code via the FQCN package path. Without this, tests
would import whatever copy of the collection is installed in the venv, which
may be stale or incomplete.
"""

import pathlib
import sys
import tempfile

_REPO = pathlib.Path(__file__).resolve().parent.parent
_ROOT = pathlib.Path(tempfile.mkdtemp(prefix="vooon-config-tests-"))
_PKG = _ROOT / "ansible_collections" / "vooon"
_PKG.mkdir(parents=True)
(_PKG / "config").symlink_to(_REPO, target_is_directory=True)
sys.path.insert(0, str(_ROOT))
