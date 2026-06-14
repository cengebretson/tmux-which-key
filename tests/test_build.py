import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "plugin"))

import build  # noqa: E402


class BuildTest(unittest.TestCase):
    def make_config(self, **overrides):
        data = {
            "command_alias_start_index": 200,
            "keybindings": {"prefix_table": "Space"},
            "items": [{"name": "Run", "key": "r", "command": "display-message run"}],
        }
        data.update(overrides)
        return build.Config(**data)

    def test_user_macro_formats_are_deferred_until_runtime(self):
        config = self.make_config(
            macros=[
                {
                    "name": "restart-pane",
                    "commands": ["respawnp -k -c #{pane_current_path}"],
                }
            ],
            items=[{"name": "Restart", "key": "R", "macro": "restart-pane"}],
        )

        generated = str(config)

        self.assertIn(
            'set -g command-alias[202] restart-pane="respawnp -k -c #{pane_current_path}"',
            generated,
        )
        self.assertNotIn("set -gF command-alias[202]", generated)

    def test_builtin_menu_aliases_expand_formats_at_source_time(self):
        generated = str(self.make_config())

        self.assertIn("set -gF command-alias[200] show-wk-menu=", generated)
        self.assertIn("set -gF command-alias[201] show-wk-menu-root=", generated)

    def test_keybindings_are_bound_synchronously(self):
        generated = str(
            self.make_config(
                keybindings={"root_table": "C-Space", "prefix_table": "Space"}
            )
        )

        self.assertIn("bind-key -Troot C-Space show-wk-menu-root", generated)
        self.assertIn("bind-key -Tprefix Space show-wk-menu-root", generated)
        self.assertNotIn("run-shell \"tmux bind-key", generated)

    def test_tmux_strings_escape_quotes_backslashes_and_newlines(self):
        config = self.make_config(
            title={"prefix": 'tmux "quoted" \\ menu', "style": "bold", "prefix_style": "fg=green"},
            custom_variables=[{"name": "log_info", "value": 'line "one"\\two\nline two'}],
            items=[{"name": 'Open "quoted"', "key": "o", "command": 'display-message "hello\\world"'}],
        )

        generated = str(config)

        self.assertIn('set -g @wk_cfg_title_prefix "tmux \\"quoted\\" \\\\ menu"', generated)
        self.assertIn('setenv -h log_info "line \\"one\\"\\\\two\\nline two"', generated)
        self.assertIn('Open \\\\\\"quoted\\\\\\"', generated)
        self.assertIn('display-message \\\\\\"hello\\\\\\\\world\\\\\\"', generated)

    def test_duplicate_menu_ids_are_rejected(self):
        with self.assertRaisesRegex(build.ConfigError, "menu ID collision"):
            self.make_config(
                items=[
                    {"name": "+Foo", "key": "f", "menu": [{"name": "One", "key": "1", "command": "display one"}]},
                    {"name": "Foo", "key": "F", "menu": [{"name": "Two", "key": "2", "command": "display two"}]},
                ]
            )

    def test_transient_item_reshows_parent_menu(self):
        generated = str(
            self.make_config(
                items=[
                    {
                        "name": "+Resize",
                        "key": "r",
                        "menu": [
                            {
                                "name": "Left",
                                "key": "h",
                                "command": "resizep -L",
                                "transient": True,
                            }
                        ],
                    }
                ]
            )
        )

        self.assertIn("resizep -L ; show-wk-menu #{@wk_menu_resize}", generated)

    def test_separator_renders_as_empty_string_entry(self):
        generated = str(
            self.make_config(
                items=[
                    {"name": "Run", "key": "r", "command": "display run"},
                    {"separator": True},
                ]
            )
        )

        # The menu option holds an escaped entry list ending in a "" separator.
        self.assertIn('set -g @wk_menu_root "Run r \\"display run\\" \\"\\""', generated)

    def test_separator_rejects_other_fields(self):
        with self.assertRaisesRegex(build.ConfigError, "separator"):
            self.make_config(items=[{"separator": True, "command": "display x"}])

    def test_invalid_position_is_rejected(self):
        with self.assertRaisesRegex(build.ConfigError, "position.x"):
            self.make_config(position={"x": "Z", "y": "P"})
        with self.assertRaisesRegex(build.ConfigError, "position.y"):
            self.make_config(position={"x": "R", "y": "Z"})

    def test_command_alias_start_index_floor_is_enforced(self):
        with self.assertRaisesRegex(build.ConfigError, "must be >= 200"):
            self.make_config(command_alias_start_index=199)

    def test_reserved_macro_name_is_rejected(self):
        with self.assertRaisesRegex(build.ConfigError, "reserved"):
            self.make_config(
                macros=[{"name": "show-wk-menu", "commands": ["display x"]}]
            )

    def test_unknown_macro_reference_is_rejected(self):
        with self.assertRaisesRegex(build.ConfigError, "unknown macro"):
            self.make_config(
                items=[{"name": "Go", "key": "g", "macro": "does-not-exist"}]
            )

    def test_validate_reads_yaml_and_rejects_duplicate_keys(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml") as config_file:
            config_file.write(
                "\n".join(
                    [
                        "command_alias_start_index: 200",
                        "keybindings:",
                        "  prefix_table: Space",
                        "items:",
                        "  - name: One",
                        "    key: o",
                        "    command: display one",
                        "    command: display two",
                    ]
                )
            )
            config_file.flush()

            with self.assertRaisesRegex(SystemExit, "duplicate key"):
                old_argv = sys.argv
                try:
                    sys.argv = ["build.py", "--validate", config_file.name]
                    build.main()
                finally:
                    sys.argv = old_argv


if __name__ == "__main__":
    unittest.main()
