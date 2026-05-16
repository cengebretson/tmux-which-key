# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

tmux-which-key is a tmux plugin that displays a customizable popup menu for discovering and executing tmux commands. Users write a YAML config; a Python builder transpiles it to a tmux script; that script is sourced at tmux startup.

## Build

The core build step converts `config.yaml` → `plugin/init.tmux`:

```bash
python3 plugin/build.py config.yaml plugin/init.tmux
```

After rebuilding, reload in a live tmux session:

```bash
tmux source-file plugin/init.tmux
```

There is no Makefile, test suite, or linter. The Python version is pinned to 3.8 (see `.python-version`); PyYAML must be installed (`python3 -m pip install pyyaml`) — it is typically pre-installed on most systems.

## Architecture

```
plugin.sh.tmux      # TPM entry point — copies example configs, runs build.py, sources init.tmux
plugin/build.py     # Python builder: parses config.yaml, emits tmux script
config.example.yaml # User-facing config template (gitignored config.yaml is the live copy)
plugin/init.tmux    # Generated output — do not edit by hand (gitignored)
```

### Data flow

1. On tmux start, `plugin.sh.tmux` runs.
2. If `config.yaml` is missing, it copies `config.example.yaml` → `config.yaml`.
3. Unless `@tmux-which-key-disable-autobuild` is set, it invokes `build.py`.
4. `build.py` reads `config.yaml`, validates it, and writes `plugin/init.tmux`.
5. `plugin.sh.tmux` sources `plugin/init.tmux` into tmux.

### build.py internals

Key classes: `Config`, `Menu`, `MenuItem`, `Macro`, `Keybindings`, `Position`, `UserOption`, `CustomVariable`.

The builder outputs three kinds of tmux constructs:
- **User options** (`@wk_cfg_*`) — runtime settings (colors, position, keybinding names)
- **Menu definitions** (`@wk_menu_*`) — stored as tmux user options, referenced by key
- **Command aliases** — macros are registered as `command-alias` entries starting at `command_alias_start_index` (≥ 200 to avoid tmux built-ins)

### Naming conventions

| Prefix | Meaning |
|---|---|
| `@wk_cfg_*` | Config user options |
| `@wk_menu_*` | Menu definition user options |
| `show-wk-menu` | Exposed tmux command aliases |

### XDG support

When `@tmux-which-key-xdg-enable` is set, the plugin reads config from `$XDG_CONFIG_HOME/tmux/plugins/tmux-which-key/` and writes generated files to `$XDG_DATA_HOME/…` instead of the plugin directory.

## Config reference

The YAML config requires:
- `command_alias_start_index` — integer ≥ 200
- `keybindings.prefix_table` — key string (e.g. `Space`)
- `items` — root menu items

Optional: `keybindings.root_table`, `title`, `position`, `custom_variables`, `macros`.

Item types: `command` (single tmux command), `submenu` (nested `Menu`), `macro` (named sequence), separator (`-`).

`transient: true` on an item re-shows the parent menu after execution (useful for resize loops).
