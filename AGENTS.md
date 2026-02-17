# AGENTS.md

## Scope
Instructions for contributors/agents working in this repository.

## Critical Rules
- User directives are absolute: if the user says `DO NOT <action>`, do not perform that action without explicit permission.
- Never edit credential/config files (for example: `clouds.yml`, `.env`) unless the user explicitly asks.
- Never fabricate or overwrite credentials.
- If the user says something is already configured, trust that statement unless they ask you to verify.
- Preserve user data and configuration. If in doubt, ask before changing.
- Do not undo user choices because you think there is a better approach without discussing first.

## Source Of Truth
- Resolve conflicts in this order:
  1. Explicit user instruction in the current task.
  2. Actual behavior of this repository's code and tests.
  3. This repository's local docs (`README.md`, plugin `DOCUMENTATION`, comments in-tree).
  4. Upstream Ansible documentation/conventions (for style, schema, and best practices).
- When local docs conflict with code, treat code/tests as authoritative and update docs.
- When code behavior is unclear or likely incorrect, consult upstream Ansible docs and call out assumptions.

## Editing Notes
- Prefer minimal, targeted patches; do not revert unrelated user changes.
- Preserve existing formatting/style in touched files unless asked to reformat.
- When adding tests, prefer the collection-native layout:
  - unit: `tests/unit/`
  - integration: `tests/integration/targets/<target_name>/tasks/main.yml`

## Commit Messages
- Typical format: `<component>: <description>`

## Testing Workflow
- Prefer `ansible-test` for plugin/collection validation.
- Keep fast Python-only checks in `pytest` unit tests.
- If both are relevant, run unit tests first, then integration tests.
- Before opening a PR with plugin/docs/changelog changes, run collection docs lint:
  `uv run antsibull-docs lint-collection-docs --plugin-docs --skip-rstcheck --validate-collection-refs=all --disallow-unknown-collection-refs .`
- If local docs lint is too slow, use the dedicated GitHub workflow (`Docs Lint`) before requesting review.
- Suggested commands:
  - `uv run pytest -q`
  - `ansible-test integration <target>`
- Note: `ansible-test` must run from a valid collection path:
  `.../ansible_collections/<namespace>/<collection>/`

## Change Hygiene
- Before finishing, report exactly which files were changed.
- Call out anything not executed (for example, tests you could not run).
- If tooling updates lock files (for example `uv.lock`) unintentionally, mention it explicitly.

## Ansible Collection Notes
- Prefer fully qualified collection names (FQCN) in new playbooks/tasks.
- Keep integration tests idempotency-focused when possible:
  first run changed, second run unchanged.
- For module changes, include check-mode behavior in tests when feasible.

## Changelog Snippets
- For user-visible changes, add an `antsibull-changelog` fragment in `changelogs/fragments/`.
- Use clear, scoped filenames, for example:
  `systemd_sysusers-check-mode.yml`.
- Keep entries short and factual, describing behavior changes and fixes.
- Skip fragments only for internal-only changes (for example, refactors/tests with no user-visible impact).
