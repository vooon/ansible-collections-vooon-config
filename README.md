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

Run docs lint:

```bash
uv run antsibull-docs lint-collection-docs --plugin-docs --skip-rstcheck --validate-collection-refs=all --disallow-unknown-collection-refs .
```

Run integration targets with `ansible-test`:

```bash
ansible-test integration systemd_sysusers
ansible-test integration systemd_tmpfiles
ansible-test integration systemd_override
ansible-test integration config_template
```

`ansible-test` must be executed from a collection path like:

```bash
.../ansible_collections/vooon/config/
```

## Release Preparation

Before cutting a release:

1. Ensure changelog fragments are present for user-visible changes:
   `changelogs/fragments/*.yml`
2. Run validation checks:

```bash
uv run pytest -q
uv run mypy --ignore-missing-imports --follow-imports skip -p plugins
uv run antsibull-docs lint-collection-docs --plugin-docs --skip-rstcheck --validate-collection-refs=all --disallow-unknown-collection-refs .
```

3. Regenerate release notes/changelog as needed:

```bash
uv run antsibull-changelog release
```

4. Bump collection version (`galaxy.yml`, `pyproject.toml`, etc.) and update lockfile if dependencies changed.
5. Build collection artifact and inspect output:

```bash
uv run ansible-galaxy collection build . --output-path dist
```

[1]: https://opendev.org/openstack/ansible-config_template/
[2]: https://github.com/sardinasystems/ansible-collections-fishos-config/
