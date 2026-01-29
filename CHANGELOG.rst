===========================
Fishos.Config Release Notes
===========================

.. contents:: Topics

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
