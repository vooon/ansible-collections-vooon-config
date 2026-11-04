Ansible Collection - vooon.config
=================================

Many year ago we modify [OpenStack's Ansible `config_template`][1] for our needs.
We have changed some logic, added support for TOML and some more things.
So it became incompatible to the original plugin.

For example we do not use remote's dest file to combine the result. We're closer to regular template.
During refactoring we've decided to split into collections and publish some of them.

NOTE: it's continuation of [`fishos.config`][2], which I have also used in my personal projects.

## Requirements

- ansible-core 2.20 or newer (see `meta/runtime.yml`)
- Python 3.14 or newer on the controller
- Python packages on the controller, depending on what you use:
  `ruamel.yaml` (YAML), `tomlkit` (TOML), `iniparse >= 0.5.3` (INI),
  `hjson` (HJSON), `jsonpatch` (JSON Patch overrides), `jsonnet`
  (`jsonnet` module), `durationpy` (`dur2sec`/`sec2dur`), `oncalendar`
  (`oncalendar`/`oncalendar_dur`)
- `systemd-sysusers` / `systemd-tmpfiles` on the target for the matching modules

## Installation

```bash
ansible-galaxy collection install git+https://github.com/vooon/ansible-collections-vooon-config.git
```

Or pin it in `requirements.yml`:

```yaml
collections:
  - name: https://github.com/vooon/ansible-collections-vooon-config.git
    type: git
    version: v3.2.0
```

## Plugins

Full option documentation lives in each plugin and can be viewed with
`ansible-doc -t <type> vooon.config.<name>`.

### Modules and action plugins

| Name | Description |
|------|-------------|
| `config_template` (alias `template`) | Render a Jinja2 template and merge `config_overrides` into the result as INI, JSON, HJSON, YAML or TOML. Overrides are a nested dict (simple merge) or an RFC 6902 JSON Patch list. |
| `jsonnet` | Render a Jsonnet template to JSON or YAML and copy it to the target. |
| `systemd_override` | Manage a drop-in override file for a system, user or quadlet unit. |
| `systemd_sysusers` | Manage a `sysusers.d` snippet and apply it with `systemd-sysusers`. |
| `systemd_tmpfiles` | Manage a `tmpfiles.d` snippet and apply it with `systemd-tmpfiles --create`. |

### Filters

| Name | Description |
|------|-------------|
| `argsenvfmt` | Join multi-line arguments into one line for a systemd `EnvironmentFile`. |
| `commentif` | Apply the `comment` filter only when a condition is true. |
| `dur2sec` / `sec2dur` | Convert between Go duration strings (`2h3m`) and seconds. |
| `nested_dict2items` | Flatten a dict of dicts into tuples of `{key, value}` items, one per nesting level. |
| `oncalendar` / `oncalendar_dur` | Next run times of a systemd `OnCalendar` spec, or the intervals between them in seconds. |
| `port` / `add_port` | Look up `service.port_name` in the `ports_overrides` and `ports` variables, optionally appending it to a host or list of hosts. |
| `url_replace` | Replace parts of a URL: path, port, or any `urlparse` field. |
| `whitespacefix` | Collapse repeated empty lines. |

### Tests

| Name | Description |
|------|-------------|
| `enabled` | True when a bool, or every item of a list, is truthy; an undefined value yields `default` (true). Handy for `when: item.when is vooon.config.enabled`. |

Example:

```yaml
- name: Render nova.conf with overrides
  vooon.config.config_template:
    src: nova.conf.j2
    dest: /etc/nova/nova.conf
    config_type: ini
    config_overrides:
      DEFAULT:
        debug: true
      database:
        connection: "mysql+pymysql://nova@db/nova"

- name: Pin the API service to a slice
  vooon.config.systemd_override:
    unit: nova-api.service
    name: slice
    content: |
      [Service]
      Slice=api.slice
```

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
ansible-test integration enabled
# The systemd_* targets write to /etc and need root, e.g. inside a container:
ANSIBLE_TEST_PREFER_PODMAN=1 ansible-test integration systemd_override --docker fedora44
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
