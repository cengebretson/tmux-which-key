PYTHON ?= python3
TMUX_BIN ?= tmux
TMUX_SOCKET ?= tmux-which-key-test
TMP_INIT ?= /tmp/tmux-which-key-init-test.tmux

.PHONY: test unit validate generated-init build shellcheck smoke clean

test: unit validate generated-init shellcheck smoke

unit:
	$(PYTHON) -m unittest discover -s tests

validate:
	$(PYTHON) plugin/build.py --validate config.example.yaml

generated-init:
	@tmp=$$(mktemp); \
	trap 'rm -f "$$tmp"' EXIT HUP INT TERM; \
	$(PYTHON) plugin/build.py config.example.yaml "$$tmp"; \
	diff -u plugin/init.example.tmux "$$tmp"

build:
	$(PYTHON) plugin/build.py config.example.yaml $(TMP_INIT)

shellcheck:
	@if command -v shellcheck >/dev/null 2>&1; then \
		shellcheck plugin.sh.tmux; \
	else \
		echo "shellcheck not installed; skipping"; \
	fi

smoke: build
	TMUX_BIN="$(TMUX_BIN)" TMUX_SOCKET="$(TMUX_SOCKET)" TMP_INIT="$(TMP_INIT)" sh -eu -c '\
		"$$TMUX_BIN" -L "$$TMUX_SOCKET" kill-server >/dev/null 2>&1 || true; \
		"$$TMUX_BIN" -L "$$TMUX_SOCKET" -f /dev/null new-session -d; \
		trap '\''"$$TMUX_BIN" -L "$$TMUX_SOCKET" kill-server >/dev/null 2>&1 || true'\'' EXIT; \
		"$$TMUX_BIN" -L "$$TMUX_SOCKET" source-file "$$TMP_INIT"; \
		"$$TMUX_BIN" -L "$$TMUX_SOCKET" list-keys -Troot | grep -qE "^bind-key +-T root C-Space +display-menu"; \
		"$$TMUX_BIN" -L "$$TMUX_SOCKET" list-keys -Tprefix | grep -qE "^bind-key +-T prefix Space +display-menu"; \
		"$$TMUX_BIN" -L "$$TMUX_SOCKET" show-options -gqv command-alias | grep -F "restart-pane=display \"#{log_info} Restarting pane\" ; respawnp -k -c #{pane_current_path}" >/dev/null; \
	'

clean:
	rm -f $(TMP_INIT)
