# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-14

### Added

- Initial release: a which-key style popup for tmux, with key tables compiled
  from a YAML config (`config.example.yaml`) by `plugin/build.py`.
- Test suite (`make test`: unit, config validation, ShellCheck, and an isolated
  tmux smoke check) and a CI workflow running it on Python 3.8 and 3.13.

[Unreleased]: https://github.com/cengebretson/tmux-which-key/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/cengebretson/tmux-which-key/releases/tag/v0.1.0
