===========================
Fishos.Config Release Notes
===========================

.. contents:: Topics

v3.1.0
======

Minor Changes
-------------

- Added ``ansible-test`` integration targets for ``systemd_tmpfiles`` and ``systemd_override`` covering idempotency and absent/check-mode behavior.
- Added an ``ansible-test`` integration target for ``systemd_sysusers`` to verify idempotency and absent/check-mode behavior.
- Modernized ``config_template`` action plugin templating flow to prefer ``Templar.template`` with compatibility fallback for older ansible-core, while keeping support for ansible-core 2.18.

Breaking Changes / Porting Guide
--------------------------------

- Dropped support for ansible-core 2.17. The collection now requires ansible-core 2.18 or newer.

Bugfixes
--------

- Updated text converter imports in ``config_template`` to use ``ansible.module_utils.common.text.converters`` when available, reducing deprecation noise on newer ansible-core versions.
- ``config_template`` now avoids mutating shared ``ansible_search_path`` task variables and reliably cleans temporary files created for ``remote_src``.
- ``systemd_override`` now creates parent directories when needed and avoids mode checks on non-existent paths in check mode.
- ``systemd_sysusers`` no longer creates ``config_dir`` for ``state=absent`` and now honors check mode for directory creation.
- ``systemd_sysusers`` now validates candidate rules with ``systemd-sysusers --dry-run`` instead of applying runtime changes during module execution.
- ``systemd_tmpfiles`` now creates ``config_dir`` only for ``state=present``, and applies rules only when content changes in non-check mode.

v3.0.0
======

Major Changes
-------------

- Add support for Ansible Core 2.20 (Ansible 13)

Breaking Changes / Porting Guide
--------------------------------

- Changed namespace. Use aliases or edit your roles.

v2.6.0
======

Release Summary
---------------

Switch to UV

Major Changes
-------------

- Import Jsonnet template from https://github.com/luqasn/ansible_jsonnet_template_action

v2.5.0
======

Release Summary
---------------

Add Quadlet overrides support

Major Changes
-------------

- `systemd_override` now has `unit_type=quadlet`, which allow placing overrides for Podman systemd units - Quadlets

v2.4.0
======

Release Summary
---------------

Release is enabled test

Major Changes
-------------

- Add enabled test, which simplifies conditions and list filtering.

v2.3.0
======

Release Summary
---------------

Add filters, documentation

Major Changes
-------------

- Add documentation to filters
- Add port, add_port, url_replace filters
- Ansible 11.3.0
- Fix documentation in modules
- Setup antsibull-docs

v2.2.0
======

Release Summary
---------------

Update to Ansible 11.2.0

v2.1.1
======

Release Summary
---------------

Update iniparse to 0.5.1

v2.1.0
======

Release Summary
---------------

Update to Ansible 11

Major Changes
-------------

- Update to Ansible 11

v2.0.0
======

Breaking Changes / Porting Guide
--------------------------------

- Alias config_template to template.
- Import some useful config filters.
- Imported back config_template from monorepo.
