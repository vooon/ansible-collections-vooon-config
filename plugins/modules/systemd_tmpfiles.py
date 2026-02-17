#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2024, Sardina Systems Ltd.
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = """
---
module: systemd_tmpfiles
short_description: Manage systemd tmpfiles
version_added: "2.0.0"
description:
  - "This module allows creating, updating and removing tmpfiles configs"

options:
  name:
    description:
      - Name of the file
    required: true
    type: str
  state:
    description:
      - Target state of the override
    type: str
    choices: [present, absent]
    default: present
  config_dir:
    description:
      - systemd tmpfiles config dir
    type: str
    default: /etc/tmpfiles.d
  content:
    description:
      - tmpfiles content
    type: str
  mode:
    description:
      - override file mode
    type: raw
    default: '0644'

extends_documentation_fragment:
  - ansible.builtin.files

author:
  - Vladimir Ermakov (@vooon)
"""

EXAMPLES = """
- name: configure files
  systemd_tmpfiles:
    name: myservice
    state: present
    content: |
        d /etc/myservice 0755 root root - -

- name: remove file
  systemd_tmpfiles:
    name: myservice
    state: absent
"""

RETURN = """
"""

from pathlib import Path  # noqa: E402 isort:skip

from ansible.module_utils.basic import AnsibleModule  # noqa: E402 isort:skip


def run_module():
    required_if = [
        ("state", "present", ["content"]),
        ("state", "absent", []),
    ]
    mutually_exclusive = []
    module_args = dict(
        name=dict(type="str", required=True),
        state=dict(
            type="str",
            choices=["present", "absent"],
            default="present",
        ),
        config_dir=dict(type="str", default="/etc/tmpfiles.d"),
        content=dict(type="str"),
        mode=dict(type="raw", default="0644"),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        required_if=required_if,
        mutually_exclusive=mutually_exclusive,
        add_file_common_args=True,
        supports_check_mode=True,
    )

    name = module.params["name"]
    state = module.params["state"]
    content = module.params["content"]
    fmode = module.params["mode"]

    dirpath = Path(module.params["config_dir"])
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
        # create config dir if needed
        if not dirpath.exists():
            changed = True
            if not module.check_mode:
                dirpath.mkdir(mode=0o755, parents=True)

        # write content to override file
        diff["after_header"] = str(filepath)
        diff["after"] = content
        content_changed = (not filepath.exists()) or (diff["before"] != content)
        if content_changed:
            changed = True
            if not module.check_mode:
                with filepath.open("wb") as fd:
                    fd.write(content.encode("utf-8"))
                module.run_command(
                    ["systemd-tmpfiles", "--create", "-"],
                    data=content,
                    check_rc=True,
                )

        if filepath.exists():
            changed = module.set_mode_if_different(filepath, fmode, changed)

    elif state == "absent":
        # remove override file
        if filepath.exists():
            changed = True
            if not module.check_mode:
                filepath.unlink()

    else:
        module.fail_json(msg="unknown state")

    module.exit_json(
        changed=changed,
        diff=diff,
    )


def main():
    run_module()


if __name__ == "__main__":
    main()
