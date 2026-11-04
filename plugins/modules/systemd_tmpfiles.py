#!/usr/bin/python
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

from pathlib import Path

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.vooon.config.plugins.module_utils.systemd_conf import (
    conf_path,
    manage_conf_file,
)


def run_module():
    required_if = [
        ("state", "present", ["content"]),
    ]
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
        add_file_common_args=True,
        supports_check_mode=True,
    )

    name = module.params["name"]
    state = module.params["state"]
    content = module.params["content"]

    filepath = conf_path(Path(module.params["config_dir"]), name)

    def apply(new_content: str) -> None:
        module.run_command(
            ["systemd-tmpfiles", "--create", "-"], data=new_content, check_rc=True
        )

    result = manage_conf_file(
        module, filepath, state=state, content=content, apply=apply
    )

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
