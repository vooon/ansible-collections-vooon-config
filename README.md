Ansible Collection - vooon.config
=================================

Many year ago we modify [OpenStack's Ansible `config_template`][1] for our needs.
We have changed some logic, added support for TOML and some more things.
So it became incompatible to the original plugin.

For example we do not use remote's dest file to combine the result. We're closer to regular template.
During refactoring we've decided to split into collections and publish some of them.

NOTE: it's continuation of [`fishos.config`][2], which I have also used in my personal projects.

## Tests

Run unit tests:

```bash
uv run pytest -q
```

Run `systemd_sysusers` integration test target:

```bash
ansible-test integration systemd_sysusers
```

[1]: https://opendev.org/openstack/ansible-config_template/
[2]: https://github.com/sardinasystems/ansible-collections-fishos-config/
