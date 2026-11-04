#!/usr/bin/python
# Copyright: (c) 2020, Sardina Systems Ltd.
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = """
---
module: systemd_override
short_description: Manage systemd overrides
version_added: "2.0.0"
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
      - Systemd unit name
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
      - Systemd config dir
      - Defaults to C(/etc/containers/systemd) if O(unit_type=quadlet)
    type: str
  unit_type:
    description:
      - Unit type
      - "V(system): place override for system unit"
      - "V(user): place override for user unit"
      - "V(quadlet): place override for podman quadlet unit"
    type: str
    choices: [system, user, quadlet]
    default: system
  content:
    description:
      - Override content
    type: str
  directory_mode:
    description:
      - Directory mode
    type: raw
    default: '0755'
  mode:
    description:
      - Override file mode
    type: raw

extends_documentation_fragment:
  - ansible.builtin.files

author:
  - Vladimir Ermakov (@vooon)
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
        unit=dict(type="str", required=True),
        state=dict(
            type="str",
            choices=["present", "absent"],
            default="present",
        ),
        prefix=dict(type="str"),
        unit_type=dict(
            type="str",
            choices=["system", "user", "quadlet"],
            default="system",
        ),
        content=dict(type="str"),
        directory_mode=dict(type="raw", default="0755"),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        required_if=required_if,
        add_file_common_args=True,
        supports_check_mode=True,
    )

    name = module.params["name"]
    unit = module.params["unit"]
    state = module.params["state"]
    content = module.params["content"]
    dmode = module.params["directory_mode"]
    prefix = module.params["prefix"]
    unit_type = module.params["unit_type"]

    if prefix is None:
        prefix = "/etc/containers/systemd" if unit_type == "quadlet" else "/etc/systemd"

    base = Path(prefix) if unit_type == "quadlet" else Path(prefix) / unit_type
    filepath = conf_path(conf_path(base, unit, suffix=".d"), name)

    result = manage_conf_file(
        module,
        filepath,
        state=state,
        content=content,
        directory_mode=dmode,
        # if there are no overrides left, remove the directory
        remove_empty_dir=True,
    )

    module.exit_json(override_file=str(filepath), **result)


def main():
    run_module()


if __name__ == "__main__":
    main()
