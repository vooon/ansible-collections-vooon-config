#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2020, SardinaSystems Ltd

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "certified",
}

DOCUMENTATION = """
---
module: systemd_override
short_description: Manage systemd overrides
version_added: "2.9"
description:
  - "This module allows to create, update and remove overrides"

options:
  name:
    description:
      - Name of the override
    required: true
    type: str
  unit:
    description:
      - systemd unit name
    required: true
    type: str
  state:
    description:
      - Target state of the override
    type: str
    choices: [present, absent]
    default: present
  prefix:
    description:
      - systemd config dir
    type: str
    default: /etc/systemd
  unit_type:
    description:
      - Unit type
    choices: [system, user]
    default: system
  content:
    description:
      - override content
    type: str
  directory_mode:
    description:
      - directory mode
    type: raw
    default: '0755'
  mode:
    description:
      - override file mode
    type: raw
    default: '0644'


author:
  - Vladimir Ermakov <vermakov@sardinasystems.com>
"""

EXAMPLES = """
- name: change slice
  systemd_override:
    unit: uwsgi@.service
    name: slice
    state: present
    content: |
      [Service]
      Slice=api.slice

- name: remove overrides
  systemd_override:
    unit: uwsgi@.service
    name: slice
    state: absent
"""

RETURN = """
override_file:
  description: File path of override config
  returned: success
  type: str
"""

from ansible.module_utils.basic import AnsibleModule  # noqa: E402 isort:skip
from ansible.module_utils.six import PY3  # noqa: E402 isort:skip

if PY3:
    from pathlib import Path
else:
    from pathlib2 import Path


def run_module():
    required_if = [
        ("state", "present", ["content"]),
        ("state", "absent", []),
    ]
    mutually_exclusive = []
    module_args = dict(
        name=dict(type="str", required=True),
        unit=dict(type="str", required=True),
        state=dict(
            type="str",
            choices=["present", "absent"],
            default="present",
        ),
        prefix=dict(type="str", default="/etc/systemd"),
        unit_type=dict(
            type="str",
            choices=["system", "user"],
            default="system",
        ),
        content=dict(type="str"),
        directory_mode=dict(type="raw"),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        required_if=required_if,
        mutually_exclusive=mutually_exclusive,
        add_file_common_args=True,
        supports_check_mode=True,
    )

    name = module.params["name"]
    unit = module.params["unit"]
    state = module.params["state"]
    content = module.params["content"]
    dmode = module.params["directory_mode"]
    fmode = module.params["mode"]

    dirpath = (
        Path(module.params["prefix"])
        / module.params["unit_type"]
        / (unit.endswith(".d") and unit or (unit + ".d"))
    )
    filepath = dirpath / (name.endswith(".conf") and name or (name + ".conf"))

    changed = False
    diff = dict(
        before_header="",
        after_header="",
        before="",
        after="",
    )

    if filepath.exists():
        diff["before_header"] = str(filepath)
        with filepath.open("r") as fd:
            diff["before"] = fd.read()

    if state == "present":
        # create override directory if needed
        if not dirpath.exists():
            changed = True
            if not module.check_mode:
                dirpath.mkdir()

        changed = module.set_mode_if_different(dirpath, dmode, changed)

        # write content to override file
        diff["after_header"] = str(filepath)
        diff["after"] = content
        if diff["before"] != content:
            changed = True
            if not module.check_mode:
                with filepath.open("wb") as fd:
                    fd.write(content.encode("utf-8"))

        changed = module.set_mode_if_different(filepath, fmode, changed)

    elif state == "absent":
        # remove override file
        if filepath.exists():
            changed = True
            if not module.check_mode:
                filepath.unlink()

        # if there is no overrides left - remove directory
        if dirpath.exists() and len(list(dirpath.iterdir())) == 0:
            changed = True
            if not module.check_mode:
                dirpath.rmdir()

    else:
        module.fail_json(msg="unknown state")

    module.exit_json(changed=changed, diff=diff, override_file=str(filepath))


def main():
    run_module()


if __name__ == "__main__":
    main()
