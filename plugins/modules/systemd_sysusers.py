#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2024, SardinaSystems Ltd

DOCUMENTATION = """
---
module: systemd_sysusers
short_description: Manage systemd sysusers
version_added: "2.0.0"
description:
  - "This module allows to create, update and remove overrides"

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
      - systemd sysusers config dir
    type: str
    default: /etc/sysusers.d
  content:
    description:
      - sysusers content
    type: str
  src:
    description:
      - file to copy
  mode:
    description:
      - override file mode
    type: raw
    default: '0644'

author:
  - Vladimir Ermakov <vermakov@sardinasystems.com>
"""

EXAMPLES = """
- name: configure files
  systemd_sysusers:
    name: myservice
    state: present
    content: |
        u haproxy 188 "HAProxy" /var/lib/haproxy

- name: remove file
  systemd_sysusers:
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
        config_dir=dict(type="str", default="/etc/sysusers.d"),
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
            # validate candidate content without mutating the system
            module.run_command(
                ["systemd-sysusers", "--dry-run", "-"],
                data=content,
                check_rc=True,
            )

            changed = True
            if not module.check_mode:
                with filepath.open("wb") as fd:
                    fd.write(content.encode("utf-8"))
                module.run_command(
                    ["systemd-sysusers", "-"],
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
