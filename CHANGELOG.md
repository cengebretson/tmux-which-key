# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-07-12

### Changed

- Internal cleanup: deduplicate the safe-character predicate in
  `plugin/build.py`, simplify a few idioms, and rename
  `home_relative_path` to `resolve_path_in_home` in `plugin.sh.tmux`
  (it returns an absolute path validated to be inside `$HOME`).
  No change to generated `init.tmux` output.
- Bump the README plugin pin example to `v0.2.0`.

## [0.2.0] - 2026-07-12

### Fixed

- Report YAML syntax errors and unreadable config files as friendly
  `[tmux-which-key] Config error:` messages instead of raw tracebacks, and stop
  labeling every top-level config `TypeError` (including missing required
  fields) as an "unexpected field".
- Reject `transient: true` on separator items as a config error instead of
  silently emitting a broken menu entry.
- Sync `config.schema.yaml` with the builder: allow `transient` on submenu
  items (the builder reopens the parent menu after the submenu command) and
  document the applied defaults for `title.style` and `title.prefix_style`.

### Removed

- The dead `@wk_cfg_key_root_table` / `@wk_cfg_key_prefix_table` user options
  from the generated init script; keybindings are emitted with literal keys
  and nothing read these options.

## [0.1.3] - 2026-07-06

### Added

- Pre-commit config (`.pre-commit-config.yaml`) running `make test`; enable
  with `pre-commit install`.

## [0.1.2] - 2026-06-17

### Fixed

- Rebuild the generated tmux init script on first install when Python is available, keeping first-load keybindings in sync with `config.example.yaml`.
- Keep `plugin/init.example.tmux` generated from `config.example.yaml` and check for drift in `make test`.
- Report nested YAML config mistakes, duplicate macro names, and unknown fields as explicit config errors.

## [0.1.1] - 2026-06-15

### Added

- A `VERSION` file and a tag-triggered release workflow that publishes a GitHub release from the changelog.

## [0.1.0] - 2026-06-14

### Added

- Initial release: a which-key style popup for tmux, with key tables compiled
  from a YAML config (`config.example.yaml`) by `plugin/build.py`.
- Test suite (`make test`: unit, config validation, ShellCheck, and an isolated
  tmux smoke check) and a CI workflow running it on Python 3.8 and 3.13.

[Unreleased]: https://github.com/cengebretson/tmux-which-key/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/cengebretson/tmux-which-key/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/cengebretson/tmux-which-key/compare/v0.1.3...v0.2.0
[0.1.3]: https://github.com/cengebretson/tmux-which-key/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/cengebretson/tmux-which-key/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/cengebretson/tmux-which-key/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/cengebretson/tmux-which-key/releases/tag/v0.1.0
