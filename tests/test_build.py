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
